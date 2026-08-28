"""ASGI entry: HTTP (Django) + WebSocket (Channels)."""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Django app must be set up before importing routing that touches models
django_asgi_app = get_asgi_application()

from apps.dialogue.middleware import ActorAuthMiddlewareStack  # noqa: E402
from apps.dialogue.routing import websocket_urlpatterns as dialogue_ws  # noqa: E402
from apps.notifications.routing import websocket_urlpatterns as notif_ws  # noqa: E402
from apps.stories.routing import websocket_urlpatterns as stories_ws  # noqa: E402

websocket_urlpatterns = dialogue_ws + notif_ws + stories_ws

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": ActorAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
