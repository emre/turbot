 ## turbot

Experimental upvote bot for steem blockchain.

#### Motivation

I have been experimenting steem-python and steem blockchain to see 
what's going on under the hood. We do have a lot of upvote bots in the scene,
yet I had no idea how they work in detail.

With the help of awesome steem-python package, I have managed to create
a simple upvote bot. @turbot

This bot is not the best bot available, and it won't be. But it can be a 
good starting point for potential steem blockchain developers.

Turbot does the following though:
- Listen the blockchain for new blocks
- Process these blocks and transactions.
- If a transaction directed to the bot account, turbot spots it and upvotes
the post in the memo.
- Turbot upvotes the related content with a random vote weight between 1-100.
- You can safely start/stop the bot. It stores the state and do not
make duplicate processing on already processed blocks.

#### Refunds

Turbot refunds SBD if:

- the post is archived
- the post is already upvoted
- transaction doesn't cover the minimum SBD
- the post URL is invalid

<img src="https://i.hizliresim.com/Qpv1L3.png">

#### Installation and Running

```
$ virtualenv -p python3 turbot
$ source turbot/bin/activate
$ git clone https://github.com/emre/turbot.git
$ vim settings.py # edit accordingly
$ cd turbot
$ PRIVATE_POSTING_KEY=[BOT_ACCOUNT_POSTING_KEY] ACTIVE_KEY=[BOT_ACCOUNT_ACTIVE_KEY] python turbot/turbot.py 
```

#### Configuration Parameters

```
MINIMUM_SBD_FOR_UPVOTE = float(0.002)
UPVOTE_WEIGHTS = (+1, +100)
BOT_ACCOUNT = 'turbot'
```

@turbot is now online for experimental usage, you can use it, it doesn't have a good STEEM power since
his wallet is very tiny but he will make sure you will get the upvote. :)

