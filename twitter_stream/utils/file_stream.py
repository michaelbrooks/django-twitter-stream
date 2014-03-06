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

logger = logging.getLogger('twitter_stream')

class ObjDict(dict):

    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        del self[item]


# the chunk size for reading in the file
PARSE_SIZE = 8 * 1024 * 1024


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
                        self.process(tweet, raw)
                        self.tweet_process_time += time.time() - start
                        tweet_count += 1

                        if self.rate_limit:
                            time_of_last_tweet = time.time()


                elif tweet_start_found == True:
                    # some line in the middle
                    raw += line

                cur_pos = infile.tell()
                if (cur_pos - last_parse_position) > PARSE_SIZE:
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
        self.listener.on_status(tweet)
        self.last_created_at = tweet['created_at']

    def start(self, interval):
        """
        Start polling for term updates and streaming.
        """

        self.polling = True

        # clear the stored list of terms - we aren't tracking any
        self.term_checker.reset()

        logger.info("Starting polling for changes to the track list")
        while self.polling:
            if self.last_created_at:
                logger.info('Inserted tweets up to %s', str(self.last_created_at))

            # Check if the tracking list has changed
            if self.term_checker.check():
                # There were changes to the term list -- restart the stream
                self.tracking_terms = self.term_checker.tracking_terms()
                self.update_stream()

            # check to see if an exception was raised in the streaming thread
            if self.listener.streaming_exception is not None:
                # propagate outward
                raise self.listener.streaming_exception

            # wait for the interval unless interrupted
            try:
                self.polling_interrupt.wait(interval)
            except KeyboardInterrupt as e:
                logger.info("Polling canceled by user")
                raise e

        logger.info("Term poll ceased!")

    def update_stream(self):
        if not self.stream:
            self.stream = threading.Thread(target=self.run)
            self.stream.start()
        else:
            logger.warn("Cannot restart fake twitter streams!")
