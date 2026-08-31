from django.urls import path

from apps.dialogue.consumers import DialogueConsumer, HelperQueueConsumer

websocket_urlpatterns = [
    path("ws/dialogues/<str:dialogue_id>/", DialogueConsumer.as_asgi()),
    path("ws/helper/queue/", HelperQueueConsumer.as_asgi()),
]
