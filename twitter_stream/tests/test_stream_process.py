from django.test import TestCase
from twitter_stream import settings
from twitter_stream.models import StreamProcess

class StreamProcessTest(TestCase):

    def test_get_memory_usage(self):
        import os

        process = StreamProcess()
        usage = process.get_memory_usage()
        if os.name == 'nt':
            self.assertEqual(usage, "Unknown")
        else:
            self.assertRegexpMatches(usage, r"\d+.\d+ MB")
