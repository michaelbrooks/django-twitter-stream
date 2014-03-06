from django.conf import settings

USE_TZ = getattr(settings, 'USE_TZ', True)

_stream_settings = getattr(settings, 'TWITTER_STREAM_SETTINGS', {})

# If true, the embedded retweeted_status tweets will be captured
CAPTURE_EMBEDDED = getattr(_stream_settings, 'CAPTURE_EMBEDDED', False)

# The number of seconds in between checks for filter term changes and tweet inserts
POLL_INTERVAL = getattr(_stream_settings, 'POLL_INTERVAL', 10)

# The default keys to use for streaming
DEFAULT_KEYS_NAME = getattr(_stream_settings, 'DEFAULT_KEYS_NAME', None)