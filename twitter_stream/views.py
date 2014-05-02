from datetime import timedelta
import json
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views import generic
from django.contrib.admin.views.decorators import staff_member_required
from jsonview.decorators import json_view
from twitter_stream.models import FilterTerm, StreamProcess
from swapper import load_model
from django.db import models


def _render_to_string_request(request, template, dictionary):
    """
    Wrapper around render_to_string that includes the request context
    This is necessary to get all of the TEMPLATE_CONTEXT_PROCESSORS
    activated in the template.
    """
    context = RequestContext(request, dictionary)
    return render_to_string(template, context_instance=context)


def stream_status():
    terms = FilterTerm.objects.filter(enabled=True)
    processes = StreamProcess.get_current_stream_processes()
    running = False
    for p in processes:
        if p.status == StreamProcess.STREAM_STATUS_RUNNING:
            running = True
            break

    Tweet = load_model("twitter_stream", "Tweet")
    tweet_count = Tweet.count_approx()
    earliest_time = Tweet.get_earliest_created_at()
    latest_time = Tweet.get_latest_created_at()

    avg_rate = None
    if earliest_time is not None and latest_time is not None:
        avg_rate = float(tweet_count) / (latest_time - earliest_time).total_seconds()

    # Get the tweets / minute over the past 10 minutes
    latest_time_minute = latest_time.replace(second=0, microsecond=0)
    tweet_counts = Tweet.objects.extra(select={
        'time': "created_at - INTERVAL SECOND(created_at) SECOND"
    }) \
        .filter(created_at__gt=latest_time_minute - timedelta(minutes=20)) \
        .values('time') \
        .order_by('time') \
        .annotate(tweets=models.Count('id'))

    tweet_counts = list(tweet_counts)

    for row in tweet_counts:
        row['time'] = row['time'].isoformat()

    return {
        'running': running,
        'terms': [t.term for t in terms],
        'processes': processes,
        'tweet_count': tweet_count,
        'earliest': earliest_time,
        'latest': latest_time,
        'avg_rate': avg_rate,
        'timeline': tweet_counts
    }



class StatusView(generic.TemplateView):
    template_name = 'twitter_stream/status.html'

    def get_context_data(self, **kwargs):
        status = stream_status()
        status['timeline'] = json.dumps(status['timeline'])
        return {
            'status': status
        }

status = staff_member_required(StatusView.as_view())

@staff_member_required
@json_view
def json_status(request, task=None):
    """
    Returns a JSON representation of the status, with
    HTML conveniently included.
    """

    status = stream_status()

    display = _render_to_string_request(request, 'twitter_stream/status_display.html', {
        'status': status
    })

    return {
        'display': display,
        'timeline': status['timeline']
    }

