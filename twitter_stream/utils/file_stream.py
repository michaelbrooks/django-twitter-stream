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
BYTES_BETWEEN_PROGRESS = 40 * 1024 * 1024


class TweetProcessor(object):
    """
    Base class for a generic tweet processor.
    Read raw json tweets from a file and run them through
    the process() function.
    """

    def __init__(self, filename, limit=None, rate_limit=None):
        self.args = ObjDict(
            tweetsfile=filename,
            limit=limit
        )

        self.tweet_read_time = 0
        self.tweet_process_time = 0
        self.tweet_parse_time = 0
        self.start_time = 0
        self.rate_limit = rate_limit


    def arguments(self, parser):
        """Add any needed arguments to the argparse parser"""
        pass


    def setup(self):
        """
        Perform any setup before processing begins.
        self.args will contain the arguments from argparse.
        """
        pass


    def process(self, tweet, raw_tweet):
        """Process the tweet. raw_tweet is the unparsed json string"""
        pass


    def teardown(self):
        """Perform any actions before the program ends."""
        pass


    def print_progress(self):
        """If there are any progress indicators, print them here."""
        pass


    def _print_progress(self):
        logger.info("--- Timing {0:0.3f}s (total) ---".format(time.time() - self.start_time))

        logger.info("  Totals: {0:0.3f}s (read) {1:0.3f}s (parse) {2:0.3f}s (process)".format(
            self.tweet_read_time, self.tweet_parse_time, self.tweet_process_time
        ))

        self.print_progress()

    def run(self):

        self.setup()

        logger.info("Parsing %s..."%(self.args.tweetsfile))
        if self.args.limit:
            logger.info("up to %d tweets..." % self.args.limit)

        with open(self.args.tweetsfile, "rt") as infile:
            self.start_time = time.time()

            # grab file size
            infile.seek(0,os.SEEK_END)
            filesize = infile.tell()
            infile.seek(0,os.SEEK_SET)

            # start our read loop with valid data
            raw = ''
            tweet_start_found = False
            start = 0
            tweet_count = 0
            last_parse_position = 0

            if self.rate_limit:
                time_of_last_tweet = time.time()
                time_between_tweets = 1.0 / self.rate_limit

            for line in infile:

                if line[0] == '{':
                    # start of tweet
                    tweet_start_found = True
                    start = time.time()
                    raw = ''
                    raw += line
                elif line[0:2] == '},' and tweet_start_found == True:
                    # end of tweet
                    raw += line[0]
                    tweet_start_found = False
                    self.tweet_read_time += time.time() - start

                    start = time.time()
                    tweet = json.loads(raw)
                    self.tweet_parse_time += time.time() - start

                    # make sure it is a tweet
                    if 'user' in tweet:

                        if self.rate_limit:
                            while time.time() - time_of_last_tweet < time_between_tweets:
                                time.sleep(time_between_tweets)

                        start = time.time()

                        if self.process(tweet, raw) is False:
                            logger.warn("Stopping file stream")
                            break

                        self.tweet_process_time += time.time() - start
                        tweet_count += 1

                        if self.rate_limit:
                            time_of_last_tweet = time.time()


                elif tweet_start_found == True:
                    # some line in the middle
                    raw += line

                cur_pos = infile.tell()
                if (cur_pos - last_parse_position) > BYTES_BETWEEN_PROGRESS:
                    last_parse_position = cur_pos
                    pct_done = (float(cur_pos) * 100.0 / float(filesize))
                    logger.info("====================")
                    logger.info("%f%% complete..."%(pct_done))
                    self._print_progress()

                if self.args.limit and self.args.limit < tweet_count:
                    break

            self.teardown()
            self._print_progress()

        logger.info("Done processing %s..."%(self.args.tweetsfile))


class FakeTwitterStream(TweetProcessor):
    """
    A tweet processor with a similar interface to the
    DynamicTweetStream class. It launches the tweet file
    reading in a separate thread.
    """
    def __init__(self, tweets_file, listener, term_checker,
                 limit=None, rate_limit=None):
        super(FakeTwitterStream, self).__init__(tweets_file, limit=limit, rate_limit=rate_limit)

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

            if self.last_created_at:
                logger.info('Inserted tweets up to %s', str(self.last_created_at))

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
