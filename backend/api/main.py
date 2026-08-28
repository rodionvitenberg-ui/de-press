"""Ninja API composition."""

from __future__ import annotations

from ninja import NinjaAPI

from api.v1 import (
    ai,
    dialogue,
    empathy,
    health,
    i18n,
    identity,
    moderation,
    notifications,
    profile,
    stories,
    support,
)

api = NinjaAPI(
    title="de-press API",
    version="1.0.0",
    urls_namespace="api",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

api.add_router("/v1", health.router)
api.add_router("/v1", identity.router)
api.add_router("/v1", stories.router)
api.add_router("/v1", empathy.router)
api.add_router("/v1", support.router)
api.add_router("/v1", moderation.router)
api.add_router("/v1", dialogue.router)
api.add_router("/v1", notifications.router)
api.add_router("/v1", profile.router)
api.add_router("/v1", ai.router)
api.add_router("/v1", i18n.router)
