from django.db import models
from datetime import datetime, timedelta
from email.utils import parsedate
from django.utils import timezone
import os
import socket
import settings
from django.core.exceptions import ObjectDoesNotExist

current_timezone = timezone.get_current_timezone()

def parse_datetime(string):
    if settings.USE_TZ:
        return datetime(*(parsedate(string)[:6]), tzinfo=current_timezone)
    else:
        return datetime(*(parsedate(string)[:6]))


class ApiKey(models.Model):
    """
    Keys for accessing the Twitter Streaming API.
    """

    created_at = models.DateTimeField(auto_now_add=True)

    name = models.CharField(max_length=250)
    email = models.EmailField(default=None, blank=True)

    api_key = models.CharField(max_length=250)
    api_secret = models.CharField(max_length=250)

    access_token = models.CharField(max_length=250)
    access_token_secret = models.CharField(max_length=250)

    def __unicode__(self):
        return self.name

    @classmethod
    def get_keys(cls, keys_name):
        if keys_name:
            keys = ApiKey.objects.get(name=keys_name)
        else:
            keys = ApiKey.objects.first()

        if not keys:
            raise ObjectDoesNotExist("Unknown keys %s" % keys_name)

        return keys

class StreamProcess(models.Model):
    """
    Tracks information about the stream process in the database.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    timeout_seconds = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    last_heartbeat = models.DateTimeField()

    keys = models.ForeignKey(ApiKey, null=True)
    hostname = models.CharField(max_length=250)
    process_id = models.PositiveIntegerField()

    STREAM_STATUS_RUNNING = "RUNNING"
    STREAM_STATUS_WAITING = "WAITING"  # No terms currently being tracked
    STREAM_STATUS_STOPPED = "STOPPED"
    status = models.CharField(max_length=10,
                              choices=(
                                  (STREAM_STATUS_RUNNING, "Running"),
                                  (STREAM_STATUS_WAITING, "Waiting"),
                                  (STREAM_STATUS_STOPPED, "Stopped")
                              ),
                              default=STREAM_STATUS_WAITING)

    tweet_rate = models.FloatField(default=0)
    error_count = models.PositiveSmallIntegerField(default=0)

    @property
    def lifetime(self):
        """Get the age of the streaming process"""
        return self.last_heartbeat - self.created_at


    def heartbeat(self, save=True):
        self.status = StreamProcess.STREAM_STATUS_RUNNING
        self.last_heartbeat = timezone.now()
        self.expires_at = self.last_heartbeat + timedelta(seconds=self.timeout_seconds)
        if save:
            self.save()

    def __unicode__(self):
        return "%s:%d %s (%s)" % (self.hostname, self.process_id, self.status, self.lifetime)

    @classmethod
    def create(cls, timeout_seconds):
        now = timezone.now()
        expires_at = now + timedelta(seconds=timeout_seconds)
        return StreamProcess(
            process_id=os.getpid(),
            hostname=socket.gethostname(),
            last_heartbeat=now,
            expires_at=expires_at,
            timeout_seconds=timeout_seconds
        )

    @classmethod
    def get_current_stream_processes(cls, minutes_ago=10):

        # some maintenance
        cls.expire_timed_out()

        minutes_ago_dt = timezone.now() - timedelta(minutes=minutes_ago)
        return StreamProcess.objects \
            .filter(last_heartbeat__gt=minutes_ago_dt) \
            .order_by('-last_heartbeat')


    @classmethod
    def expire_timed_out(cls):
        StreamProcess.objects \
            .filter(expires_at__lt=timezone.now()) \
            .update(status=StreamProcess.STREAM_STATUS_STOPPED)


class Tweet(models.Model):
    """
    Selected fields from a Twitter Status object.
    Incorporates several fields from the associated User object.

    For details see https://dev.twitter.com/docs/platform-objects/tweets

    Note that we are not using tweet_id as a primary key -- this application
    does not enforce integrity w/ regard to individual tweets.
    We just add them to the database as they come in, even if we've seen
    them before.
    """

    # Basic tweet info
    tweet_id = models.BigIntegerField()
    text = models.CharField(max_length=250)
    truncated = models.BooleanField()
    lang = models.CharField(max_length=9, null=True, blank=True, default=None)

    # Basic user info
    user_id = models.BigIntegerField()
    user_screen_name = models.CharField(max_length=50)
    user_name = models.CharField(max_length=150)
    user_verified = models.BooleanField()

    # Timing parameters
    created_at = models.DateTimeField()  # should be UTC
    user_utc_offset = models.IntegerField(null=True, blank=True, default=None)
    user_time_zone = models.CharField(max_length=150, null=True, blank=True, default=None)

    # none, low, or medium
    filter_level = models.CharField(max_length=6, null=True, blank=True, default=None)

    # Geo parameters
    latitude = models.FloatField(null=True, blank=True, default=None)
    longitude = models.FloatField(null=True, blank=True, default=None)
    user_geo_enabled = models.BooleanField(default=False)
    user_location = models.CharField(max_length=150, null=True, blank=True, default=None)

    # Engagement - not likely to be very useful for streamed tweets but whatever
    favorite_count = models.PositiveIntegerField(null=True, blank=True)
    retweet_count = models.PositiveIntegerField(null=True, blank=True)
    user_followers_count = models.PositiveIntegerField(null=True, blank=True)
    user_friends_count = models.PositiveIntegerField(null=True, blank=True)

    # Relation to other tweets
    in_reply_to_status_id = models.BigIntegerField(null=True, blank=True, default=None)
    retweeted_status_id = models.BigIntegerField(null=True, blank=True, default=None)

    # Track the number of analyses that have already considered this tweet
    analyzed_by = models.SmallIntegerField(default=0)

    @classmethod
    def create_from_json(cls, raw):
        """
        Given a *parsed* json status object, construct a new Tweet model.
        """

        user = raw['user']
        retweeted_status = raw.get('retweeted_status', {'id': None})

        # The "coordinates" entry looks like this:
        #
        # "coordinates":
        # {
        #     "coordinates":
        #     [
        #         -75.14310264,
        #         40.05701649
        #     ],
        #     "type":"Point"
        # }

        coordinates = (None, None)
        if raw['coordinates']:
            coordinates = raw['coordinates']['coordinates']

        return cls(
            # Basic tweet info
            tweet_id=raw['id'],
            text=raw['text'],
            truncated=raw['truncated'],
            lang=raw.get('lang'),

            # Basic user info
            user_id=user['id'],
            user_screen_name=user['screen_name'],
            user_name=user['name'],
            user_verified=user['verified'],

            # Timing parameters
            created_at=parse_datetime(raw['created_at']),
            user_utc_offset=user.get('utc_offset'),
            user_time_zone=user.get('time_zone'),

            # none, low, or medium
            filter_level=raw.get('filter_level'),

            # Geo parameters
            latitude=coordinates[1],
            longitude=coordinates[0],
            user_geo_enabled=user.get('geo_enabled'),
            user_location=user.get('location'),

            # Engagement - not likely to be very useful for streamed tweets but whatever
            favorite_count=raw.get('favorite_count'),
            retweet_count=raw.get('retweet_count'),
            user_followers_count=user.get('followers_count'),
            user_friends_count=user.get('friends_count'),

            # Relation to other tweets
            in_reply_to_status_id=raw.get('in_reply_to_status_id'),
            retweeted_status_id=retweeted_status['id']
        )

    @classmethod
    def get_created_in_range(cls, start, end):
        """
        Returns all the tweets between start and end.
        """
        return cls.objects.filter(created_at__gte=start, created_at__lt=end)

    @classmethod
    def get_earliest_created_at(cls):
        """
        Returns the earliest created_at time, or None
        """
        result = cls.objects.aggregate(earliest_created_at=models.Min('created_at'))
        return result['earliest_created_at']

    @classmethod
    def get_latest_created_at(cls):
        """
        Returns the latest created_at time, or None
        """
        result = cls.objects.aggregate(latest_created_at=models.Max('created_at'))
        return result['latest_created_at']


class FilterTerm(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    term = models.CharField(max_length=250)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.term
