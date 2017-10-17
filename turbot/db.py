from os.path import expanduser, exists
from os import makedirs

TURBOT_PATH = expanduser('~/.turbot')
UPVOTE_LOGS = expanduser("%s/upvote_logs" % TURBOT_PATH)
CHECKPOINT = expanduser("%s/checkpoint" % TURBOT_PATH)
REFUND_LOG = expanduser("%s/refunds" % TURBOT_PATH)


def load_checkpoint(fallback_block_num=None):
    try:
        return int(open(CHECKPOINT).read())
    except FileNotFoundError as e:
        if not exists(TURBOT_PATH):
            makedirs(TURBOT_PATH)

        dump_checkpoint(fallback_block_num)
        return load_checkpoint()


def dump_checkpoint(block_num):
    f = open(CHECKPOINT, 'w+')
    f.write(str(block_num))
    f.close()


def load_refunds():
    try:
        refunds = open(REFUND_LOG).readlines()
        refunds = [r.replace("\n", "") for r in refunds]
    except FileNotFoundError as e:
        if not exists(TURBOT_PATH):
            makedirs(TURBOT_PATH)
        f = open(REFUND_LOG, 'w+')
        f.close()
        refunds = []

    return refunds


def refund_key(to, memo, amount):
    return "%s-%s-%s" % (to, memo, amount)


def add_refund(to, memo, amount):
    f = open(REFUND_LOG, 'a+')
    f.write(refund_key(to, memo, amount))
    f.close()


def already_refunded(to, memo, amount):
    refunds = load_refunds()
    return refund_key(to, memo, amount) in refunds
