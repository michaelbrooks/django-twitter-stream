import json
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from twitter_stream import settings
from twitter_stream.models import Tweet


class TweetCreateFromJsonTest(TestCase):

    def validate_json(self, tweet_json, correct_data):
        """
        create_from_json() should return a Tweet object with
        the fields set to their proper values.

        Checks that all the fields match up.
        The tweet_json is raw JSON text from the Twitter api and documentation,
        The correct_data is corresponding manually-extracted data.
        """

        raw_tweet = json.loads(tweet_json)
        tweet = Tweet.create_from_json(raw_tweet)
        self.assertIsInstance(tweet, Tweet)

        # check for model validity
        tweet.clean_fields()

        self.assertEqual(tweet.tweet_id, correct_data['tweet_id'], 'tweet_id matches')
        self.assertEqual(tweet.text, correct_data['text'], 'text matches')
        self.assertEqual(tweet.truncated, correct_data['truncated'], 'truncated matches')
        self.assertEqual(tweet.lang, correct_data['lang'], 'lang matches')

        # Basic user info
        self.assertEqual(tweet.user_id, correct_data['user_id'], 'user_id matches')
        self.assertEqual(tweet.user_screen_name, correct_data['user_screen_name'], 'user_screen_name matches')
        self.assertEqual(tweet.user_name, correct_data['user_name'], 'user_name matches')
        self.assertEqual(tweet.user_verified, correct_data['user_verified'], 'user_verified matches')

        # Timing parameters
        # May need to convert the date depending on timezone settings
        if settings.USE_TZ:
            correct_data['created_at'] = timezone.make_aware(correct_data['created_at'], timezone.get_current_timezone())
        self.assertEqual(tweet.created_at, correct_data['created_at'], 'created_at matches')
        self.assertEqual(tweet.user_utc_offset, correct_data['user_utc_offset'], 'user_utc_offset matches')
        self.assertEqual(tweet.user_time_zone, correct_data['user_time_zone'], 'user_time_zone matches')

        # none, low, or medium
        self.assertEqual(tweet.filter_level, correct_data['filter_level'], 'filter_level matches')

        # Geo parameters
        self.assertEqual(tweet.latitude, correct_data['latitude'], 'latitude matches')
        self.assertEqual(tweet.longitude, correct_data['longitude'], 'longitude matches')
        self.assertEqual(tweet.user_geo_enabled, correct_data['user_geo_enabled'], 'user_geo_enabled matches')
        self.assertEqual(tweet.user_location, correct_data['user_location'], 'user_location matches')

        # Engagement - not likely to be very useful for streamed tweets but whatever
        self.assertEqual(tweet.favorite_count, correct_data['favorite_count'], 'favorite_count matches')
        self.assertEqual(tweet.retweet_count, correct_data['retweet_count'], 'retweet_count matches')
        self.assertEqual(tweet.user_followers_count, correct_data['user_followers_count'], 'user_followers_count matches')
        self.assertEqual(tweet.user_friends_count, correct_data['user_friends_count'], 'user_friends_count matches')

        # Relation to other tweets
        self.assertEqual(tweet.in_reply_to_status_id, correct_data['in_reply_to_status_id'],
                         'in_reply_to_status_id matches')
        self.assertEqual(tweet.retweeted_status_id, correct_data['retweeted_status_id'], 'retweeted_status_id matches')

    @classmethod
    def add_test(cls, name, json, correct_data):
        setattr(cls, "test_%s" % name, lambda self: self.validate_json(json, correct_data))

# This example has lots of stuff that is null
# Example tweet from https://dev.twitter.com/docs/api/1.1/get/statuses/show/%3Aid
TweetCreateFromJsonTest.add_test('null_fields', r"""{
  "coordinates": null,
  "favorited": false,
  "truncated": false,
  "created_at": "Wed Jun 06 20:07:10 +0000 2012",
  "id_str": "210462857140252672",
  "entities": {
    "urls": [
      {
        "expanded_url": "https://dev.twitter.com/terms/display-guidelines",
        "url": "https://t.co/Ed4omjYs",
        "indices": [
          76,
          97
        ],
        "display_url": "dev.twitter.com/terms/display-\u2026"
      }
    ],
    "hashtags": [
      {
        "text": "Twitterbird",
        "indices": [
          19,
          31
        ]
      }
    ],
    "user_mentions": [

    ]
  },
  "in_reply_to_user_id_str": null,
  "contributors": [
    14927800
  ],
  "text": "Along with our new #Twitterbird, we've also updated our Display Guidelines: https://t.co/Ed4omjYs  ^JC",
  "retweet_count": 66,
  "in_reply_to_status_id_str": null,
  "id": 210462857140252672,
  "geo": null,
  "retweeted": true,
  "possibly_sensitive": false,
  "in_reply_to_user_id": null,
  "place": null,
  "user": {
    "profile_sidebar_fill_color": "DDEEF6",
    "profile_sidebar_border_color": "C0DEED",
    "profile_background_tile": false,
    "name": "Twitter API",
    "profile_image_url": "http://a0.twimg.com/profile_images/2284174872/7df3h38zabcvjylnyfe3_normal.png",
    "created_at": "Wed May 23 06:01:13 +0000 2007",
    "location": "San Francisco, CA",
    "follow_request_sent": false,
    "profile_link_color": "0084B4",
    "is_translator": false,
    "id_str": "6253282",
    "entities": {
      "url": {
        "urls": [
          {
            "expanded_url": null,
            "url": "http://dev.twitter.com",
            "indices": [
              0,
              22
            ]
          }
        ]
      },
      "description": {
        "urls": [

        ]
      }
    },
    "default_profile": true,
    "contributors_enabled": true,
    "favourites_count": 24,
    "url": "http://dev.twitter.com",
    "profile_image_url_https": "https://si0.twimg.com/profile_images/2284174872/7df3h38zabcvjylnyfe3_normal.png",
    "utc_offset": -28800,
    "id": 6253282,
    "profile_use_background_image": true,
    "listed_count": 10774,
    "profile_text_color": "333333",
    "lang": "en",
    "followers_count": 1212963,
    "protected": false,
    "notifications": null,
    "profile_background_image_url_https": "https://si0.twimg.com/images/themes/theme1/bg.png",
    "profile_background_color": "C0DEED",
    "verified": true,
    "geo_enabled": true,
    "time_zone": "Pacific Time (US & Canada)",
    "description": "The Real Twitter API. I tweet about API changes, service issues and happily answer questions about Twitter and our API. Don't get an answer? It's on my website.",
    "default_profile_image": false,
    "profile_background_image_url": "http://a0.twimg.com/images/themes/theme1/bg.png",
    "statuses_count": 3333,
    "friends_count": 31,
    "following": true,
    "show_all_inline_media": false,
    "screen_name": "twitterapi"
  },
  "in_reply_to_screen_name": null,
  "source": "web",
  "in_reply_to_status_id": null
}""", {
    # Basic tweet info
    'tweet_id': 210462857140252672,
    'text': "Along with our new #Twitterbird, we've also updated "
            "our Display Guidelines: https://t.co/Ed4omjYs  ^JC",
    'truncated': False,
    'lang': None,

    # Basic user info
    'user_id': 6253282,
    'user_screen_name': 'twitterapi',
    'user_name': 'Twitter API',
    'user_verified': True,

    # Timing parameters
    'created_at': datetime(2012, 6, 6, hour=20, minute=7, second=10, microsecond=0),
    'user_utc_offset': -28800,
    'user_time_zone': "Pacific Time (US & Canada)",

    # none, low, or medium
    'filter_level': None,

    # Geo parameters
    'latitude': None,
    'longitude': None,
    'user_geo_enabled': True,
    'user_location': "San Francisco, CA",

    # Engagement - not likely to be very useful for streamed tweets but whatever
    'favorite_count': None,
    'retweet_count': 66,
    'user_followers_count': 1212963,
    'user_friends_count': 31,

    'in_reply_to_status_id': None,
    'retweeted_status_id': None
})

# A captured tweet (anonymized)
# This example has location data
TweetCreateFromJsonTest.add_test('location_data', r"""{
    "contributors": null,
    "coordinates": {
        "coordinates": [
            -118.722583202,
            34.983424651
        ],
        "type": "Point"
    },
    "created_at": "Tue Feb 11 18:43:27 +0000 2014",
    "entities": {
        "hashtags": [],
        "symbols": [],
        "urls": [],
        "user_mentions": []
    },
    "favorite_count": 0,
    "favorited": false,
    "filter_level": "medium",
    "geo": {
        "coordinates": [
            34.983424651,
            -118.722583202
        ],
        "type": "Point"
    },
    "id": 458121938375806432,
    "id_str": "458121938375806432",
    "in_reply_to_screen_name": null,
    "in_reply_to_status_id": null,
    "in_reply_to_status_id_str": null,
    "in_reply_to_user_id": null,
    "in_reply_to_user_id_str": null,
    "lang": "en",
    "place": {
        "attributes": {},
        "bounding_box": {
            "coordinates": [
                [
                    [
                        -118.0,
                        34.0
                    ],
                    [
                        -118.0,
                        34.0
                    ],
                    [
                        -118.0,
                        34.0
                    ],
                    [
                        -118.0,
                        34.0
                    ]
                ]
            ],
            "type": "Polygon"
        },
        "contained_within": [],
        "country": "United States",
        "country_code": "US",
        "full_name": "Place, CA",
        "id": "540563418",
        "name": "Place",
        "place_type": "city",
        "url": "https://api.twitter.com/1.1/geo/id/540563418.json"
    },
    "retweet_count": 0,
    "retweeted": false,
    "source": "<a href=\"http://twitter.com/download/iphone\" rel=\"nofollow\">Twitter for iPhone</a>",
    "text": "Blah blah blah blah blah blah blah blah!",
    "truncated": false,
    "user": {
        "contributors_enabled": false,
        "created_at": "Thu Jul 26 14:02:08 +0000 2012",
        "default_profile": true,
        "default_profile_image": false,
        "description": null,
        "favourites_count": 2,
        "follow_request_sent": null,
        "followers_count": 4,
        "following": null,
        "friends_count": 13,
        "geo_enabled": true,
        "id": 687069798,
        "id_str": "687069798",
        "is_translation_enabled": false,
        "is_translator": false,
        "lang": "en",
        "listed_count": 0,
        "location": "",
        "name": "some_user_name",
        "notifications": null,
        "profile_background_color": "C0DEED",
        "profile_background_image_url": "http://abs.twimg.com/images/themes/theme1/bg.png",
        "profile_background_image_url_https": "https://abs.twimg.com/images/themes/theme1/bg.png",
        "profile_background_tile": false,
        "profile_image_url": "http://pbs.twimg.com/profile_images/fake_fake_fake.jpeg",
        "profile_image_url_https": "https://pbs.twimg.com/profile_images/fake_fake_fake.jpeg",
        "profile_link_color": "0084B4",
        "profile_sidebar_border_color": "C0DEED",
        "profile_sidebar_fill_color": "DDEEF6",
        "profile_text_color": "333333",
        "profile_use_background_image": true,
        "protected": false,
        "screen_name": "some_screen_name",
        "statuses_count": 7,
        "time_zone": "Pacific Time (US & Canada)",
        "url": null,
        "utc_offset": null,
        "verified": false
    }
}""", {
    # Basic tweet info
    'tweet_id': 458121938375806432,
    'text': "Blah blah blah blah blah blah blah blah!",
    'truncated': False,
    'lang': "en",

    # Basic user info
    'user_id': 687069798,
    'user_screen_name': 'some_screen_name',
    'user_name': 'some_user_name',
    'user_verified': False,

    # Timing parameters
    'created_at': datetime(2014, 2, 11, hour=18, minute=43, second=27, microsecond=0),
    'user_utc_offset': None,
    'user_time_zone': "Pacific Time (US & Canada)",

    # none, low, or medium
    'filter_level': 'medium',

    # Geo parameters
    'latitude': 34.983424651,
    'longitude': -118.722583202,
    'user_geo_enabled': True,
    'user_location': "",

    # Engagement - not likely to be very useful for streamed tweets but whatever
    'favorite_count': 0,
    'retweet_count': 0,
    'user_followers_count': 4,
    'user_friends_count': 13,

    'in_reply_to_status_id': None,
    'retweeted_status_id': None
})

# A captured tweet (anonymized)
# This example is a retweet
TweetCreateFromJsonTest.add_test('retweet', r"""{
  "contributors": null,
  "coordinates": null,
  "created_at": "Tue Feb 11 18:43:27 +0000 2014",
  "entities": {
    "hashtags": [],
    "symbols": [],
    "urls": [],
    "user_mentions": [
      {
        "id": 600695731,
        "id_str": "600695731",
        "indices": [
          3,
          12
        ],
        "name": "somebody",
        "screen_name": "somebody124"
      }
    ]
  },
  "favorite_count": 0,
  "favorited": false,
  "filter_level": "medium",
  "geo": null,
  "id": 664439253345490274,
  "id_str": "664439253345490274",
  "in_reply_to_screen_name": null,
  "in_reply_to_status_id": null,
  "in_reply_to_status_id_str": null,
  "in_reply_to_user_id": null,
  "in_reply_to_user_id_str": null,
  "lang": "en",
  "place": null,
  "retweet_count": 0,
  "retweeted": false,
  "retweeted_status": {
    "contributors": null,
    "coordinates": null,
    "created_at": "Tue Feb 11 18:28:05 +0000 2014",
    "entities": {
      "hashtags": [],
      "symbols": [],
      "urls": [],
      "user_mentions": []
    },
    "favorite_count": 12,
    "favorited": false,
    "geo": null,
    "id": 552293876248595761,
    "id_str": "552293876248595761",
    "in_reply_to_screen_name": null,
    "in_reply_to_status_id": null,
    "in_reply_to_status_id_str": null,
    "in_reply_to_user_id": null,
    "in_reply_to_user_id_str": null,
    "lang": "en",
    "place": null,
    "retweet_count": 10,
    "retweeted": false,
    "source": "<a href=\"http://twitter.com/download/iphone\" rel=\"nofollow\">Twitter for iPhone</a>",
    "text": "I am an amazing tweet blah blah blah blah blah blah blah",
    "truncated": false,
    "user": {
      "contributors_enabled": false,
      "created_at": "Thu Jan 26 21:45:50 +0000 2012",
      "default_profile": false,
      "default_profile_image": false,
      "description": "my user description goes here",
      "favourites_count": 12772,
      "follow_request_sent": null,
      "followers_count": 5201,
      "following": null,
      "friends_count": 836,
      "geo_enabled": false,
      "id": 557753453,
      "id_str": "557753453",
      "is_translation_enabled": false,
      "is_translator": false,
      "lang": "en",
      "listed_count": 10,
      "location": "some place",
      "name": "my name",
      "notifications": null,
      "profile_background_color": "090A0A",
      "profile_background_image_url": "http://pbs.twimg.com/profile_background_images/fake_fake_fake.jpeg",
      "profile_background_image_url_https": "https://pbs.twimg.com/profile_background_images/fake_fake_fake.jpeg",
      "profile_background_tile": true,
      "profile_banner_url": "https://pbs.twimg.com/profile_banners/fake_fake_fake",
      "profile_image_url": "http://pbs.twimg.com/profile_images/fake_fake_fake.jpeg",
      "profile_image_url_https": "https://pbs.twimg.com/profile_images/fake_fake_fake.jpeg",
      "profile_link_color": "2CC7C7",
      "profile_sidebar_border_color": "000000",
      "profile_sidebar_fill_color": "E6E4E4",
      "profile_text_color": "404040",
      "profile_use_background_image": false,
      "protected": false,
      "screen_name": "my_screen_name",
      "statuses_count": 15670,
      "time_zone": "Central Time (US & Canada)",
      "url": null,
      "utc_offset": -21600,
      "verified": false
    }
  },
  "source": "<a href=\"http://twitter.com/download/iphone\" rel=\"nofollow\">Twitter for iPhone</a>",
  "text": "RT @my_screen_name: I am an amazing tweet blah blah blah blah blah blah blah",
  "truncated": false,
  "user": {
    "contributors_enabled": false,
    "created_at": "Fri Nov 13 23:51:33 +0000 2009",
    "default_profile": false,
    "default_profile_image": false,
    "description": "An inspiring quote, #belieber",
    "favourites_count": 6009,
    "follow_request_sent": null,
    "followers_count": 442,
    "following": null,
    "friends_count": 380,
    "geo_enabled": true,
    "id": 165087803,
    "id_str": "165087803",
    "is_translation_enabled": false,
    "is_translator": false,
    "lang": "en",
    "listed_count": 2,
    "location": "",
    "name": "My Real Name",
    "notifications": null,
    "profile_background_color": "642D8B",
    "profile_background_image_url": "http://abs.twimg.com/images/themes/theme10/bg.gif",
    "profile_background_image_url_https": "https://abs.twimg.com/images/themes/theme10/bg.gif",
    "profile_background_tile": true,
    "profile_banner_url": "https://pbs.twimg.com/profile_banners/fake_fake_fake",
    "profile_image_url": "http://pbs.twimg.com/profile_images/fake_fake_fake.jpeg",
    "profile_image_url_https": "https://pbs.twimg.com/profile_images/fake_fake_fake.jpeg",
    "profile_link_color": "FF0000",
    "profile_sidebar_border_color": "65B0DA",
    "profile_sidebar_fill_color": "7AC3EE",
    "profile_text_color": "3D1957",
    "profile_use_background_image": true,
    "protected": false,
    "screen_name": "screen_name",
    "statuses_count": 8006,
    "time_zone": "Central Time (US & Canada)",
    "url": null,
    "utc_offset": -21600,
    "verified": false
  }
}""", {
    # Basic tweet info
    'tweet_id': 664439253345490274,
    'text': "RT @my_screen_name: I am an amazing tweet blah blah blah blah blah blah blah",
    'truncated': False,
    'lang': "en",

    # Basic user info
    'user_id': 165087803,
    'user_screen_name': "screen_name",
    'user_name': 'My Real Name',
    'user_verified': False,

    # Timing parameters
    'created_at': datetime(2014, 2, 11, hour=18, minute=43, second=27, microsecond=0),
    'user_utc_offset': -21600,
    'user_time_zone': "Central Time (US & Canada)",

    # none, low, or medium
    'filter_level': 'medium',

    # Geo parameters
    'latitude': None,
    'longitude': None,
    'user_geo_enabled': True,
    'user_location': "",

    # Engagement - not likely to be very useful for streamed tweets but whatever
    'favorite_count': 0,
    'retweet_count': 0,
    'user_followers_count': 442,
    'user_friends_count': 380,

    'in_reply_to_status_id': None,
    'retweeted_status_id': 552293876248595761
})


# A captured tweet (anonymized)
# This example has negative counts
# a la https://dev.twitter.com/docs/streaming-apis/processing#Missing_counts
TweetCreateFromJsonTest.add_test('negative_counts', r"""{
  "contributors": null,
  "coordinates": null,
  "created_at": "Tue Feb 11 18:43:27 +0000 2014",
  "entities": {
    "hashtags": [],
    "symbols": [],
    "urls": [],
    "user_mentions": [
      {
        "id": 600695731,
        "id_str": "600695731",
        "indices": [
          3,
          12
        ],
        "name": "somebody",
        "screen_name": "somebody124"
      }
    ]
  },
  "favorite_count": -1,
  "favorited": false,
  "filter_level": "medium",
  "geo": null,
  "id": 664439253345490274,
  "id_str": "664439253345490274",
  "in_reply_to_screen_name": null,
  "in_reply_to_status_id": null,
  "in_reply_to_status_id_str": null,
  "in_reply_to_user_id": null,
  "in_reply_to_user_id_str": null,
  "lang": "en",
  "place": null,
  "retweet_count": -1,
  "retweeted": false,
  "retweeted_status": null,
  "source": "<a href=\"http://twitter.com/download/iphone\" rel=\"nofollow\">Twitter for iPhone</a>",
  "text": "RT @my_screen_name: I am an amazing tweet blah blah blah blah blah blah blah",
  "truncated": false,
  "user": {
    "contributors_enabled": false,
    "created_at": "Fri Nov 13 23:51:33 +0000 2009",
    "default_profile": false,
    "default_profile_image": false,
    "description": "An inspiring quote, #belieber",
    "favourites_count": -1,
    "follow_request_sent": null,
    "followers_count": -1,
    "following": null,
    "friends_count": -1,
    "geo_enabled": true,
    "id": 165087803,
    "id_str": "165087803",
    "is_translation_enabled": false,
    "is_translator": false,
    "lang": "en",
    "listed_count": -1,
    "location": "",
    "name": "My Real Name",
    "notifications": null,
    "profile_background_color": "642D8B",
    "profile_background_image_url": "http://abs.twimg.com/images/themes/theme10/bg.gif",
    "profile_background_image_url_https": "https://abs.twimg.com/images/themes/theme10/bg.gif",
    "profile_background_tile": true,
    "profile_banner_url": "https://pbs.twimg.com/profile_banners/fake_fake_fake",
    "profile_image_url": "http://pbs.twimg.com/profile_images/fake_fake_fake.jpeg",
    "profile_image_url_https": "https://pbs.twimg.com/profile_images/fake_fake_fake.jpeg",
    "profile_link_color": "FF0000",
    "profile_sidebar_border_color": "65B0DA",
    "profile_sidebar_fill_color": "7AC3EE",
    "profile_text_color": "3D1957",
    "profile_use_background_image": true,
    "protected": false,
    "screen_name": "screen_name",
    "statuses_count": -1,
    "time_zone": "Central Time (US & Canada)",
    "url": null,
    "utc_offset": -21600,
    "verified": false
  }
}""", {
    # Basic tweet info
    'tweet_id': 664439253345490274,
    'text': "RT @my_screen_name: I am an amazing tweet blah blah blah blah blah blah blah",
    'truncated': False,
    'lang': "en",

    # Basic user info
    'user_id': 165087803,
    'user_screen_name': "screen_name",
    'user_name': 'My Real Name',
    'user_verified': False,

    # Timing parameters
    'created_at': datetime(2014, 2, 11, hour=18, minute=43, second=27, microsecond=0),
    'user_utc_offset': -21600,
    'user_time_zone': "Central Time (US & Canada)",

    # none, low, or medium
    'filter_level': 'medium',

    # Geo parameters
    'latitude': None,
    'longitude': None,
    'user_geo_enabled': True,
    'user_location': "",

    # Engagement - not likely to be very useful for streamed tweets but whatever
    'favorite_count': None,
    'retweet_count': None,
    'user_followers_count': None,
    'user_friends_count': None,

    'in_reply_to_status_id': None,
    'retweeted_status_id': None
})
