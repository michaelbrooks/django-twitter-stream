Django Twitter Stream
=====================

A Django app for streaming tweets from the Twitter API into a database.

You can start a streaming process which will insert
Tweets into the database as they are delivered
by Twitter. The process monitors a table of "filter terms" which
you can update over time if you want.

This app uses the [tweepy](http://github.com/tweepy/tweepy) library
for connecting to the Twitter API.


Installation
------------

Install with pip:

```bash
pip -e git+https://github.com/michaelbrooks/django-twitter-stream.git#egg=django-twitter-stream
```

Add to `INSTALLED_APPS` in your Django settings file:

```python
INSTALLED_APPS = (
    # other apps
    "twitter_stream",
)
```

Run `python manage.py syncdb` to update your database.
You need to supply your Twitter API keys and set up some filter terms
before you can stream tweets. Instructions for this follow.


### Provide Twitter API Keys

Once you have added `twitter_stream` to your list of installed apps,
the Django Admin page should include a section for the `API_Key` model.
You can use this to input your Twitter API keys.

If you do not have Twitter API keys, you must sign in to the
[Twitter Developers site](http://dev.twitter.com). Next, go to
your [applications list](https://dev.twitter.com/apps). If you do
not have an application already, create one.
Once you have created an application, go to the "API Keys" area,
scroll to the bottom, and click the button to generate access keys for your account.
This can take a few minutes to complete.

Once you have an application and access keys for your account,
you can copy the necessary values into a new API_Keys entry.
This includes the "API key" and "API secret", located at the
top of your application keys page, and
the "Access Token" and "Access Token Secret", located at
the bottom of your application keys page.


### Customize the Filter Terms

Currently, this package uses the `filter` endpoint of the
Twitter Streaming API ([more info](https://dev.twitter.com/docs/streaming-apis/streams/public)).
This endpoint accepts a set of tracking terms. Any tweets matching these terms
will be delivered to you as they are created (approximately).
The precise behavior of term filtering is described [here](https://dev.twitter.com/docs/streaming-apis/parameters#track).

This package defines a FilterTerm model. You can add filter
terms to this table through the Django Admin interface,
or through code. When you change the terms in the database,
the stream will briefly shut itself down and then restart
with the new list.

If there are no terms in your database, the connection to Twitter will be
closed until some terms are available. Note that connecting to the unfiltered
public stream is not yet supported.

Due to Twitter's rate limit, the Streaming API appears to return
all of the tweets matching your filter terms *up to* around 1%
of the total volume on Twitter at the present moment.
In my experience, you will get at most around 50 or 60 tweets per second.


Start the Streaming Process
---------------------------

To start the streaming process, use the `stream` management command:

```bash
$ python manage.py stream
```

This will connect to Twitter using API keys and tracking terms from your database.

If you have stored multiple API keys in your database, you may select a particular
set of API keys by name as an argument to this command:

You may also choose the rate at which the database will be polled for changes
to the filter terms. This is also the interval at which tweets will be batch-inserted
into your database, so don't set it too long. The default is 10 seconds.

```bash
$ python manage.py stream MyAPIKeys --poll-interval 30
```

*Warning*: Twitter does not allow an account to open more than one streaming
 connection at a time. If you repeatedly try to open too many streaming connections,
 there may be repercussions. If you start receiving disconnect errors from Twitter,
 take a break for a few minutes before trying to reconnect.


Settings
--------

Settings for this app can be configured by adding the `TWITTER_STREAM_SETTINGS` to your
Django settings file. Below are the default settings:

```python
TWITTER_STREAM_SETTINGS = {

    # Set to True to save embedded retweeted_status tweets. Normally these are discarded.
    'CAPTURE_EMBEDDED': False,

    # Change the default term track and tweet insert interval
    'POLL_INTERVAL': 10,

    # The name of the default keys to use for streaming. If not set, we'll just grab one.
    'DEFAULT_KEYS_NAME': None,
}
```

Streaming From a File
---------------------

There is also a `stream_from_file` command provided which can parse
a file containing already collected tweets. This can be handy for debugging.
This is an experimental feature.


Questions and Contributing
--------------------------

Feel free to post questions and problems on the issue tracker. Pull requests welcome!
