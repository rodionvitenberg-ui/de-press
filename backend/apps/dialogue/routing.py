from django.urls import path

from apps.dialogue.consumers import DialogueConsumer

websocket_urlpatterns = [
    path("ws/dialogues/<str:dialogue_id>/", DialogueConsumer.as_asgi()),
]
