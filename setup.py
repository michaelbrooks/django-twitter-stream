import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-twitter-stream',
    version='0.1.1',
    packages=['twitter_stream'],
    url='http://github.com/michaelbrooks/django-twitter-stream',
    license='MIT',
    author='Michael Brooks',
    author_email='mjbrooks@uw.edu',
    description='A Django app for streaming tweets from the Twitter API into a database.',
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=[
        "django >= 1.6, < 1.7",
        "twitter-monitor >= 0.2.1, < 0.3",
        "swapper >= 0.1.1, < 0.2",
        "django-jsonview >= 0.2, < 0.5",
        "django-bootstrap3 >= 4.3.0"
    ],
    test_suite="setuptest.setuptest.SetupTestSuite",
    tests_require=[
        'django-setuptest',
    ]
)
