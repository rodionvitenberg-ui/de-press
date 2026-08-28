from django.urls import path

from apps.stories.consumers import FeedConsumer

websocket_urlpatterns = [
    path("ws/feed/", FeedConsumer.as_asgi()),
]
