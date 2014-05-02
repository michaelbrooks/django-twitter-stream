"""
Parses a file containing pretty-printed json objects as produced by Twitter.

For example:
{
    ... some tweet json
},
{
    ... some other tweet json
},
"""

import time
import os
import json
import logging
import threading

import twitter_monitor

logger = logging.getLogger(__name__)

class ObjDict(dict):

    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        del self[item]

class FakeTermChecker(twitter_monitor.TermChecker):

    def __init__(self, queue_listener, stream_process):
        super(FakeTermChecker, self).__init__()

        # A queue for tweets that need to be written to the database
        self.listener = queue_listener
        self.error_count = 0
        self.process = stream_process

    def check(self):
        """We always return true!"""

        # Process the tweet queue -- this is more important
        # to do regularly than updating the tracking terms
        # Update the process status in the database
        self.process.tweet_rate = self.listener.process_tweet_queue()
        self.process.error_count = self.error_count
        self.process.heartbeat()

        return True

    def ok(self):
        return self.error_count < 5

    def error(self, exc):
        logger.error(exc)
        self.error_count += 1

# the chunk size for reading in the file
TWEETS_BETWEEN_PROGRESS = 7000

class FakeTwitterStream(object):
    """
    A tweet processor with a similar interface to the
    DynamicTweetStream class. It launches the tweet file
    reading in a separate thread.
    """
    def __init__(self, tweets_file, listener, term_checker,
                 limit=None, rate_limit=None, pretty=False):

        self.tweets_file = tweets_file

        self.limit = limit
        self.rate_limit = rate_limit
        self.pretty = pretty

        self.listener = listener
        self.term_checker = term_checker

        self.tracking_terms = []
        self.polling = False
        self.stream = None
        self.last_created_at = 0

        self.polling_interrupt = threading.Event()

    def process(self, tweet, raw_tweet):
        self.last_created_at = tweet['created_at']
        return self.listener.on_status(tweet)

    def next_tweet_pretty(self, infile):
        # start our read loop with valid data

        raw = ''
        tweet_start_found = False

        while True:
            try:
                line = next(infile)
            except StopIteration:
                return None

            if line[0] == '{':
                # start of tweet
                tweet_start_found = True
                raw = ''
                raw += line
            elif line[0:2] == '},' and tweet_start_found == True:
                # end of tweet
                raw += line[0]
                tweet_start_found = False

                return raw

            elif tweet_start_found == True:
                # some line in the middle
                raw += line

    def next_tweet(self, infile):
        return next(infile, None)

    def run(self):

        logger.info("Parsing %s..." % self.tweets_file)
        if self.limit:
            logger.info("up to %d tweets..." % self.limit)

        if hasattr(self.tweets_file, 'read'):
            infile = self.tweets_file
        else:
            infile = open(self.tweets_file, "rt")

        tweet_count = 0
        last_report_count = 0

        if self.rate_limit:
            time_of_last_tweet = time.time()
            time_between_tweets = 1.0 / self.rate_limit

        while True:
            if self.pretty:
                raw = self.next_tweet_pretty(infile)
            else:
                raw = self.next_tweet(infile)

            if not raw:
                break

            tweet = json.loads(raw)

            # make sure it is a tweet
            if 'user' in tweet:

                if self.rate_limit:
                    while time.time() - time_of_last_tweet < time_between_tweets:
                        time.sleep(time_between_tweets)

                if self.process(tweet, raw) is False:
                    logger.warn("Stopping file stream")
                    break

                tweet_count += 1

                if self.rate_limit:
                    time_of_last_tweet = time.time()

            if tweet_count - last_report_count > TWEETS_BETWEEN_PROGRESS:
                last_report_count = tweet_count

                logger.info("Read in %d tweets", tweet_count)
                if self.last_created_at:
                    logger.info('Inserted tweets up to %s', str(self.last_created_at))

            if self.limit and self.limit < tweet_count:
                logger.info("Limit of %d reached.", self.limit)
                break

        logger.info("Read in %d tweets (total)", tweet_count)
        if self.last_created_at:
            logger.info('Tweets stopped at %s', str(self.last_created_at))
        logger.info("Done reading file.")

    def start_polling(self, interval):
        """
        Start polling for term updates and streaming.
        """

        self.polling = True

        # clear the stored list of terms - we aren't tracking any
        self.term_checker.reset()

        logger.info("Starting polling for changes to the track list")
        while self.polling:
            loop_start = time.time()

            self.update_stream()
            self.handle_exceptions()

            # wait for the interval (compensate for the time taken in the loop
            elapsed = (time.time() - loop_start)
            self.polling_interrupt.wait(max(0.1, interval - elapsed))

        logger.warn("Term poll ceased!")

    def update_stream(self):
        """
        Restarts the stream with the current list of tracking terms.
        """

        # Check if the tracking list has changed
        if not self.term_checker.check():
            return

        # Start a new stream
        self.start_stream()

    def start_stream(self):
        """
        Starts a stream if not already started.
        """

        if not self.stream:
            self.stream = threading.Thread(target=self.run)
            self.stream.start()

    def handle_exceptions(self):
        # check to see if an exception was raised in the streaming thread
        if self.listener.streaming_exception is not None:
            logger.warn("Streaming exception: %s", self.listener.streaming_exception)
            # propagate outward
            raise self.listener.streaming_exception
