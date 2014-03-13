# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ApiKey'
        db.create_table(u'twitter_stream_apikey', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('email', self.gf('django.db.models.fields.EmailField')(default=None, max_length=75, blank=True)),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('api_secret', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('access_token', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('access_token_secret', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal(u'twitter_stream', ['ApiKey'])

        # Adding model 'StreamProcess'
        db.create_table(u'twitter_stream_streamprocess', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('timeout_seconds', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('expires_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('last_heartbeat', self.gf('django.db.models.fields.DateTimeField')()),
            ('keys', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['twitter_stream.ApiKey'], null=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('process_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('status', self.gf('django.db.models.fields.CharField')(default='WAITING', max_length=10)),
            ('tweet_rate', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('error_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'twitter_stream', ['StreamProcess'])

        # Adding model 'Tweet'
        db.create_table(u'twitter_stream_tweet', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tweet_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('truncated', self.gf('django.db.models.fields.BooleanField')()),
            ('lang', self.gf('django.db.models.fields.CharField')(default=None, max_length=9, null=True, blank=True)),
            ('user_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('user_screen_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('user_name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('user_verified', self.gf('django.db.models.fields.BooleanField')()),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('user_utc_offset', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('user_time_zone', self.gf('django.db.models.fields.CharField')(default=None, max_length=150, null=True, blank=True)),
            ('filter_level', self.gf('django.db.models.fields.CharField')(default=None, max_length=6, null=True, blank=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
            ('user_geo_enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user_location', self.gf('django.db.models.fields.CharField')(default=None, max_length=150, null=True, blank=True)),
            ('favorite_count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('retweet_count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('user_followers_count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('user_friends_count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('in_reply_to_status_id', self.gf('django.db.models.fields.BigIntegerField')(default=None, null=True, blank=True)),
            ('retweeted_status_id', self.gf('django.db.models.fields.BigIntegerField')(default=None, null=True, blank=True)),
            ('analyzed_by', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'twitter_stream', ['Tweet'])

        # Adding model 'FilterTerm'
        db.create_table(u'twitter_stream_filterterm', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('term', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'twitter_stream', ['FilterTerm'])


    def backwards(self, orm):
        # Deleting model 'ApiKey'
        db.delete_table(u'twitter_stream_apikey')

        # Deleting model 'StreamProcess'
        db.delete_table(u'twitter_stream_streamprocess')

        # Deleting model 'Tweet'
        db.delete_table(u'twitter_stream_tweet')

        # Deleting model 'FilterTerm'
        db.delete_table(u'twitter_stream_filterterm')


    models = {
        u'twitter_stream.apikey': {
            'Meta': {'object_name': 'ApiKey'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'access_token_secret': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'api_secret': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': 'None', 'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'twitter_stream.filterterm': {
            'Meta': {'object_name': 'FilterTerm'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'term': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'twitter_stream.streamprocess': {
            'Meta': {'object_name': 'StreamProcess'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'error_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'expires_at': ('django.db.models.fields.DateTimeField', [], {}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keys': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['twitter_stream.ApiKey']", 'null': 'True'}),
            'last_heartbeat': ('django.db.models.fields.DateTimeField', [], {}),
            'process_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'WAITING'", 'max_length': '10'}),
            'timeout_seconds': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tweet_rate': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'twitter_stream.tweet': {
            'Meta': {'object_name': 'Tweet'},
            'analyzed_by': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            'favorite_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'filter_level': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_reply_to_status_id': ('django.db.models.fields.BigIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'retweet_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'retweeted_status_id': ('django.db.models.fields.BigIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'truncated': ('django.db.models.fields.BooleanField', [], {}),
            'tweet_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'user_followers_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user_friends_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user_geo_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'user_location': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'user_screen_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'user_time_zone': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'user_utc_offset': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'user_verified': ('django.db.models.fields.BooleanField', [], {})
        }
    }

    complete_apps = ['twitter_stream']