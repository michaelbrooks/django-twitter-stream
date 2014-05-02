import Queue
import logging
import time
import json

import twitter_monitor
from twitter_stream import settings, models
from swapper import load_model

__all__ = ['FeelsTermChecker', 'QueueStreamListener']

logger = logging.getLogger(__name__)


class TweetQueue(Queue.Queue):
    """
    Simply extends the Queue class with get_all methods.
    """

    def get_all(self, block=True, timeout=None):
        """Remove and return all the items from the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).
        """
        self.not_empty.acquire()
        try:
            if not block:
                if not self._qsize():
                    raise Queue.Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                endtime = time.time() + timeout
                while not self._qsize():
                    remaining = endtime - time.time()
                    if remaining <= 0.0:
                        raise Queue.Empty
                    self.not_empty.wait(remaining)
            items = self._get_all()
            self.not_full.notify()
            return items
        finally:
            self.not_empty.release()

    def get_all_nowait(self):
        """Remove and return all the items from the queue without blocking.

        Only get items if immediately available. Otherwise
        raise the Empty exception.
        """
        return self.get_all(False)

    def _get_all(self):
        """
        Get all the items from the queue.
        """
        result = []
        while len(self.queue):
            result.append(self.queue.popleft())
        return result


class FeelsTermChecker(twitter_monitor.TermChecker):
    """
    Checks the database for filter terms.

    Note that because this is run every now and then, and
    so as not to block the streaming thread, this
    object will actually also insert the tweets into the database.
    """

    def __init__(self, queue_listener, stream_process):
        super(FeelsTermChecker, self).__init__()

        # A queue for tweets that need to be written to the database
        self.listener = queue_listener
        self.error_count = 0
        self.process = stream_process

    def update_tracking_terms(self):

        # Process the tweet queue -- this is more important
        # to do regularly than updating the tracking terms
        # Update the process status in the database
        self.process.tweet_rate = self.listener.process_tweet_queue()
        self.process.error_count = self.error_count

        # Check for new tracking terms
        filter_terms = models.FilterTerm.objects.filter(enabled=True)

        if len(filter_terms):
            self.process.status = models.StreamProcess.STREAM_STATUS_RUNNING
        else:
            self.process.status = models.StreamProcess.STREAM_STATUS_WAITING

        self.process.heartbeat()

        return set([t.term for t in filter_terms])

    def ok(self):
        return self.error_count < 5

    def error(self, exc):
        logger.error(exc)
        self.error_count += 1


class QueueStreamListener(twitter_monitor.JsonStreamListener):
    """
    Saves tweets in a queue for later insertion into database
    when process_tweet_batch() is called.

    Note that this is operated by the streaming thread.
    """

    def __init__(self, api=None, to_file=None):
        """
        Listens for tweets from Tweepy and saves them in the database
        when process_tweet_queue() is called (in a separate thread, probably).

        If to_file is given, tweets are written to the file instead.
        JSON formatted, one per line.
        """
        super(QueueStreamListener, self).__init__(api)

        self.terminate = False

        # A place to put the tweets
        self.queue = TweetQueue()

        # For calculating tweets / sec
        self.time = time.time()

        # Place for saving tweets if not in the database.
        self.to_file = to_file
        self._output_file = None

    def on_status(self, status):
        # construct a Tweet object from the raw status object.
        self.queue.put_nowait(status)

        # If terminate gets set, this should take out the tweepy stream thread
        return not self.terminate

    def process_tweet_queue(self):
        """
        Inserts any queued tweets into the database.

        It is ok for this to be called on a thread other than the streaming thread.
        """

        # this is for calculating the tps rate
        now = time.time()
        diff = now - self.time
        self.time = now

        try:
            batch = self.queue.get_all_nowait()
        except Queue.Empty:
            return 0

        if len(batch) == 0:
            return 0

        Tweet = load_model("twitter_stream", "Tweet")

        tweets = []
        for status in batch:
            if settings.CAPTURE_EMBEDDED and 'retweeted_status' in status:
                if self.to_file:
                    tweets.append(json.dumps(status['retweeted_status']))
                else:
                    tweets.append(Tweet.create_from_json(status['retweeted_status']))

            if self.to_file:
                if 'retweeted_status' in status:
                    del status['retweeted_status']

                tweets.append(json.dumps(status))
            else:
                tweets.append(Tweet.create_from_json(status))

        if tweets:
            if self.to_file:
                if not self._output_file or self._output_file.closed:
                    self._output_file = open(self.to_file, 'ab')
                self._output_file.write("\n".join(tweets) + "\n")
                self._output_file.flush()
                logger.info("Dumped %s tweets at %s tps to %s" % (len(tweets), len(tweets) / diff, self.to_file))
            else:
                Tweet.objects.bulk_create(tweets, settings.INSERT_BATCH_SIZE)
                logger.info("Inserted %s tweets at %s tps" % (len(tweets), len(tweets) / diff))
        else:
            logger.info("Saved 0 tweets")

        if settings.DEBUG:
            # Prevent apparent memory leaks
            # https://docs.djangoproject.com/en/dev/faq/models/#why-is-django-leaking-memory
            from django import db
            db.reset_queries()

        return len(tweets) / diff

    def set_terminate(self):
        self.terminate = True
