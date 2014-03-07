import logging
from optparse import make_option
from logging.config import dictConfig
import time
import signal

from django.core.management.base import BaseCommand
import tweepy
import twitter_monitor
from twitter_stream import models
from twitter_stream import utils
from twitter_stream import settings


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
    Starts a process that streams data from Twitter.

    Example usage:
    python manage.py stream
    python manage.py stream --poll-interval 25
    python manage.py stream MyCredentialsName
    """

    option_list = BaseCommand.option_list + (
        make_option(
            '--poll-interval',
            action='store',
            dest='poll_interval',
            default=settings.POLL_INTERVAL,
            help='Seconds between term updates and tweet inserts.'
        ),
    )
    args = '<keys_name>'
    help = "Starts a streaming connection to Twitter"

    def handle(self, keys_name=settings.DEFAULT_KEYS_NAME, *args, **options):

        # The suggested time between hearbeats
        poll_interval = options.get('poll_interval', settings.POLL_INTERVAL)

        # First expire any old stream process records that have failed
        # to report in for a while
        timeout_seconds = 3 * poll_interval
        models.StreamProcess.expire_timed_out()

        # Create the stream process for tracking ourselves
        stream_process = models.StreamProcess.create(
            timeout_seconds=timeout_seconds
        )

        # Expire old stream processes that may be lying around
        models.StreamProcess.expire_timed_out()

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
            keys = models.ApiKey.get_keys(keys_name)

            logger.info("Using keys for %s", keys.name)
            stream_process.keys = keys
            stream_process.save()

            auth = tweepy.OAuthHandler(keys.api_key, keys.api_secret)
            auth.set_access_token(keys.access_token, keys.access_token_secret)

            listener = utils.QueueStreamListener()
            checker = utils.FeelsTermChecker(queue_listener=listener,
                                             stream_process=stream_process)

            # Start and maintain the streaming connection...
            stream = twitter_monitor.DynamicTwitterStream(auth, listener, checker)

            while checker.ok():
                try:
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
