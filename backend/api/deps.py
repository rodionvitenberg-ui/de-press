"""Ninja dependencies: Actor resolution."""

from __future__ import annotations

from django.http import HttpRequest

from apps.identity.services import Actor, require_actor, resolve_actor


def get_optional_actor(request: HttpRequest) -> Actor:
    return resolve_actor(request)


def get_actor(request: HttpRequest) -> Actor:
    """Actor that can write; mints AnonymousSession if needed."""
    return require_actor(request)
