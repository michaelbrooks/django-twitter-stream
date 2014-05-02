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
pip install -e git+https://github.com/michaelbrooks/django-twitter-stream.git#egg=django-twitter-stream
```

Add to `INSTALLED_APPS` in your Django settings file:

```python
INSTALLED_APPS = (
    # other apps
    "twitter_stream",
)
```

Run `python manage.py syncdb` to update your database.
This project also supports migrations with [South](http://south.aeracode.org/).
If you are using South in your project, you should run `python manage.py migrate`.

You need to supply your Twitter API keys and set up some filter terms
before you can stream tweets. Instructions for this follow.


### Provide Twitter API Keys

Once you have added `twitter_stream` to your list of installed apps,
the Django Admin page should include a section for the `ApiKey` model.
You can use this to input your Twitter API keys.

If you do not have Twitter API keys, you must sign in to the
[Twitter Developers site](http://dev.twitter.com). Next, go to
your [applications list](https://dev.twitter.com/apps). If you do
not have an application already, create one.
Once you have created an application, go to the "API Keys" area,
scroll to the bottom, and click the button to generate access keys for your account.
This can take a few minutes to complete.

Once you have an application and access keys for your account,
you can copy the necessary values into a new ApiKey entry.
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

> *Warning*: Twitter does not allow an account to open more than one streaming
 connection at a time. If you repeatedly try to open too many streaming connections,
 there may be repercussions. If you start receiving disconnect errors from Twitter,
 take a break for a few minutes before trying to reconnect.

If you need to take your database offline for some reason or just want to stream
tweets to a file instead, you can use the `--to-file` option:

```bash
$ python manage.py stream --to-file some_file.json
```

This will append tweets, in JSON format, one-per-line, to "some_file.json".
If you are capturing retweets, they will be separated out onto separate lines.
If you are not, they will be removed from the JSON objects before being printed.

You may also configure the stream to read from a file (or stdin with '-'):

```bash
$ python manage.py stream --from-file some_file.json
$ python manage.py stream --from-file -
```

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

    # Put the stream in a loop so random termination will be prevented.
    'PREVENT_EXIT': False,
}
```

Status Page
-----------

This app provides a status page that shows how the Twitter stream is doing.
Just add something like this to your url conf:

```python
    url(r'^stream/', include('twitter_stream.urls', namespace="twitter_stream")),
```

Custom Tweet Classes
--------------------

It is possible to swap the provided Tweet class for your own, so that you
can add other fields or whatever.
To do this, in the models.py file for your app (which we will call 'myapp' in this example),
add a class that extends `AbstractTweet`:

```python
from twitter_stream.models import AbstractTweet
class MyTweet(AbstractTweet):
    """ add whatever here... """
```

Then, add this to your settings file:
```python
TWITTER_STREAM_TWEET_MODEL = 'myapp.MyTweet'
```

This is facilitated by the [django-swappable-models](https://github.com/wq/django-swappable-models) package.

Anywhere you were previously hard-importing the Tweet model,
you will need to replace it with something like this:

```python
from swapper import load_model
Tweet = load_model('twitter_stream', 'Tweet')
```

This will load either the original Tweet model or the swapped model
as appropriate. You can also load your `MyTweet` model directly, of course.

For creating foreign keys pointing to Tweet (or the swapped model)
you can use `swapper.get_model_name('twitter_stream', 'Tweet')`.

If you are using South migrations and need to migrate from the old Tweet model
to your new model, [this tutorial](http://www.caktusgroup.com/blog/2013/08/07/migrating-custom-user-model-django/)
explains the issues. The basic idea is to do it in these steps:

1. Create your new model and change your model loading throughout (i.e. use `load_model`),
   but don't set the `TWITTER_STREAM_TWEET_MODEL` to actually swap it out yet.
2. Create a normal schema migration on `myapp` to make the database table for
   your new model. Run the migration.
3. Write a data migration that copies data from the old `twitter_stream_tweets` table to your new table.
   Run the data migration.
4. Trick South into creating a migration for you that you can use to delete the old table with the `SOUTH_MIGRATION_MODULES` setting.
   This step may need adaptation to work with `django-twitter-stream` since it was designed for the migration-less
   `django.contrib.auth` app.
5. Finally, swap the models with the `TWITTER_STREAM_TWEET_MODEL` setting.
6. Generate new schema migrations for any apps with foreign keys that reference the Tweet model.
7. Move your stub migration that deletes the twitter_stream_tweets table into your app's migration queue.
8. Run all the remaining migrations.

Streaming From a File
---------------------

There is also a `stream_from_file` command provided which can parse
a file containing already collected tweets. This can be handy for debugging.
This feature is deprecated. The `stream` command now provides this functionality.


Questions and Contributing
--------------------------

Feel free to post questions and problems on the issue tracker. Pull requests welcome!
