from os.path import abspath, dirname, join, normpath

# Absolute filesystem path to the Django project directory:
DJANGO_ROOT = dirname(dirname(abspath(__file__)))


SECRET_KEY = 'secret'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_database.db',
    }
}

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    normpath(join(DJANGO_ROOT, 'templates')),
)

INSTALLED_APPS = (
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'bootstrap3',
    'twitter_stream',
    'south',
)