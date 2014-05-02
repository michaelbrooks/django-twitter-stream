from django.conf.urls import patterns, url

urlpatterns = patterns('twitter_stream.views',
                       url(r'^$', 'status', name='status'),
                       url(r'^update/', 'json_status', name='update'),
)
