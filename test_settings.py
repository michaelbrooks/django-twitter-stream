SECRET_KEY = 'secret'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_database.db',
    }
}

INSTALLED_APPS = (
    'twitter_stream',
    'south',
)