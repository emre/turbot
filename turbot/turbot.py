import logging
import os
import time
import random

import db
import settings

from steem import Steem
from steem.commit import Commit
from steem.post import Post
from steembase.exceptions import VotingInvalidOnArchivedPost

logger = logging.getLogger('turbot')
logger.setLevel(logging.DEBUG)
logging.basicConfig()

PRIVATE_POSTING_KEY = os.environ['PRIVATE_POSTING_KEY']
ACTIVE_KEY = os.environ['ACTIVE_KEY']


class TransactionListener(object):

    def __init__(self, steem):
        self.steem = steem
        self.commit = Commit(steem)
        self.watch_account = settings.BOT_ACCOUNT

    @property
    def last_irreversible_block_num(self):
        props = self.steem.get_dynamic_global_properties()
        if not props:
            logger.info('Couldnt get block num. Retrying.')
            return self.last_irreversible_block_num
        return props['last_irreversible_block_num']

    @property
    def block_interval(self):
        config = self.steem.get_config()
        return config["STEEMIT_BLOCK_INTERVAL"]

    @property
    def upvote_weight(self):
        min_weight, max_weight = settings.UPVOTE_WEIGHTS
        return float(random.randint(min_weight, max_weight))

    def process_block(self, block_id, retry_count=0):

        block_data = self.steem.get_block(block_id)

        if not block_data:
            if retry_count > 3:
                logger.error(
                    'Retried 3 times to get this block: %s Skipping.',
                    block_id
                )
                return

            logger.error(
                'Couldnt read the block: %s. Retrying.', block_id)
            self.process_block(block_id, retry_count=retry_count + 1)

        logger.info('Processing block: %s', block_id)

        if 'transactions' not in block_data:
            return

        for tx in block_data['transactions']:
            for operation in tx['operations']:
                operation_type, operation_data = operation[0:2]
                if operation_type == 'transfer':
                    self.process_transfer(
                        operation_data, block_data, block_id)

    def process_transfer(self, op, block_data, block_id):
        if op["to"] == self.watch_account:
            logger.info(
                "%d | %s | %s -> %s: %s -- %s" % (
                    block_id,
                    block_data["timestamp"],
                    op["from"],
                    op["to"],
                    op["amount"],
                    op["memo"]
                )
            )
            if "SBD" in op['amount']:
                amount_in_float = float(op['amount'].split(' ')[0])
                if amount_in_float < settings.MINIMUM_SBD_FOR_UPVOTE:
                    self.refund(
                        op, 'Minimum SBD for upvote: %s' %
                        settings.MINIMUM_SBD_FOR_UPVOTE)
                    return
                self.upvote(op)
            else:
                logger.info(
                    'There is a transfer but its not SBD. Ignoring.')

    def refund(self, op, message):
        refund_key = db.refund_key(op['from'], op['memo'], op['amount'])
        if db.already_refunded(op['from'], op['memo'], op['amount']):
            logger.info('This is already refunded. Skipping. %s', refund_key)
            return
        refund_amount, asset = op['amount'].split(' ')

        if float(refund_amount) > 0.5:
            logger.error('Too much for a auto-refund. Skipping.')
            return

        self.commit.transfer(
            op['from'],
            float(refund_amount),
            memo=message,
            asset=asset,
            account=self.watch_account
        )
        logger.info('Refunded %s for invalid request.', op['from'])
        db.add_refund(op['from'], op['memo'], op['amount'])

    def upvote(self, op):
        try:
            post = Post(op['memo'])
        except ValueError:
            logger.info('Invalid identifier: %s', op['memo'])
            self.refund(op, message='invalid url')
            return
        try:
            weight = self.upvote_weight

            post.upvote(weight=weight, voter=self.watch_account)

        except VotingInvalidOnArchivedPost as e:
            logger.info('Archived post. Cannot upvote. %s', op['memo'])
            self.refund(
                op, message='Couldnt vote. Archived post. %s' % op['memo'])
            return
        except Exception as e:
            if 'already voted' in e.args[0]:
                self.refund(op, message='Already upvoted. %s' % op['memo'])
            logger.info('Already voted: %s. Skipping.', op['memo'])
            return
        logger.info('Upvoted %s with weight: %s', op['memo'], weight)

    def run(self):
        last_block = db.load_checkpoint(
            fallback_block_num=self.last_irreversible_block_num,
        )
        logger.info('Last processed block: %s', last_block)
        while True:

            while (self.last_irreversible_block_num - last_block) > 0:
                last_block += 1
                self.process_block(last_block)
                db.dump_checkpoint(last_block)

            # Sleep for one block
            block_interval = self.block_interval
            logger.info('Sleeping for %s seconds.', block_interval)
            time.sleep(block_interval)


if __name__ == '__main__':
    logger.info('Starting Transaction Listener')
    steem = Steem(keys=[PRIVATE_POSTING_KEY, ACTIVE_KEY])
    tx_listener = TransactionListener(steem)
    tx_listener.run()
