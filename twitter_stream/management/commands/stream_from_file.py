import logging
from optparse import make_option
from logging.config import dictConfig

import time

from django.core.management.base import BaseCommand
import signal

from twitter_stream import models
from twitter_stream import utils

# Setup logging if not already configured
logger = logging.getLogger('twitter_stream')

if not logger.handlers:
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "twitter_stream": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                },
            },
        "twitter_stream": {
            "handlers": ["twitter_stream"],
            "level": "DEBUG"
        }
    })


class Command(BaseCommand):
    """
    Streams tweets from an existing file. The file should
    be pretty-printed JSON dump from the streaming API.

    Example usage:
    python manage.py stream_from_file tweets.json
    python manage.py stream_from_file tweets.json --limit 100000
    python manage.py stream_from_file tweets.json --rate-limit 25 --poll-interval 25
    """

    option_list = BaseCommand.option_list + (
        make_option(
            '--poll-interval',
            action='store',
            dest='poll_interval',
            default=10,
            type=int,
            help='Seconds between tweet inserts.'
        ),
        make_option(
            '--rate-limit',
            action='store',
            dest='rate_limit',
            default=None,
            type=float,
            help='Rate to read in tweets.'
        ),
        make_option(
            '--limit',
            action='store',
            dest='limit',
            default=None,
            type=int,
            help='Limit the number of tweets read.'
        )
    )
    args = '<tweets_file>'
    help = "Fakes a streaming connection to twitter by reading from a file."

    def handle(self, tweets_file=None, *args, **options):

        # The suggested time between hearbeats
        poll_interval = options.get('poll_interval', 10)
        rate_limit = options.get('rate_limit', 50)
        limit = options.get('limit', None)

        # First expire any old stream process records that have failed
        # to report in for a while
        timeout_seconds = 3 * poll_interval
        models.StreamProcess.expire_timed_out()

        stream_process = models.StreamProcess.create(
            timeout_seconds=3 * poll_interval
        )

        def stop(signum, frame):
            """
            Register stream's death and exit.
            """
            logger.debug("Stopping because of signal")

            if stream_process:
                stream_process.status = models.StreamProcess.STREAM_STATUS_STOPPED
                stream_process.heartbeat()

            raise SystemExit()

        # Installs signal handlers for handling SIGINT and SIGTERM
        # gracefully.
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

        try:

            logger.info("Streaming from %s", tweets_file)
            if rate_limit:
                logger.info("Rate limit: %f", rate_limit)

            listener = utils.QueueStreamListener()
            checker = utils.FeelsTermChecker(queue_listener=listener,
                                                 stream_process=stream_process)

            while checker.ok():
                try:
                    # Start and maintain the streaming connection...
                    stream = utils.FakeTwitterStream(tweets_file,
                                               limit=limit, rate_limit=rate_limit,
                                               listener=listener, term_checker=checker)

                    stream.start(poll_interval)
                except Exception as e:
                    checker.error(e)
                    time.sleep(1)  # to avoid craziness

            logger.error("Stopping because of excess errors")
            stream_process.status = models.StreamProcess.STREAM_STATUS_STOPPED
            stream_process.heartbeat()

        except Exception as e:
            logger.error(e)

        finally:
            stop(None, None)
