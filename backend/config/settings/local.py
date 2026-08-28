"""Local development settings.

Primary database: system PostgreSQL `depress` (see POSTGRES_* in repo `.env`).
SQLite is allowed only for pytest (or explicit DEPRESS_ALLOW_SQLITE_DEV=1).
"""

from __future__ import annotations

import logging
import os
import sys
import warnings

from .base import *  # noqa: F403

DEBUG = True

logger = logging.getLogger("depress.db")


def _is_pytest_runtime() -> bool:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return True
    if "pytest" in sys.modules:
        return True
    return any("pytest" in arg for arg in sys.argv)


_use_sqlite = os.environ.get("DEPRESS_USE_SQLITE", "").lower() in ("1", "true", "yes")
_allow_sqlite_dev = os.environ.get("DEPRESS_ALLOW_SQLITE_DEV", "").lower() in (
    "1",
    "true",
    "yes",
)

if _use_sqlite:
    if not _is_pytest_runtime() and not _allow_sqlite_dev:
        raise RuntimeError(
            "DEPRESS_USE_SQLITE is only for pytest. "
            "Local app must use the system Postgres database 'depress' "
            "(POSTGRES_* in repo .env). Unset DEPRESS_USE_SQLITE, "
            "or set DEPRESS_ALLOW_SQLITE_DEV=1 to force SQLite outside tests."
        )
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }
    if not _is_pytest_runtime():
        warnings.warn(
            "Running with SQLite (DEPRESS_ALLOW_SQLITE_DEV). "
            "This is not the project default; data will not appear in Postgres 'depress'.",
            stacklevel=1,
        )

# Prefer in-memory channel layer for local SQLite / pytest unless Redis forced
if os.environ.get("CHANNEL_LAYER", "").lower() == "memory" or (
    _use_sqlite and (_is_pytest_runtime() or _allow_sqlite_dev)
):
    CHANNEL_LAYERS = {  # noqa: F405
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }

# One-line startup orientation (visible when logging is configured)
_db = DATABASES["default"]  # noqa: F405
_engine = _db.get("ENGINE", "")
if "postgresql" in _engine:
    logger.info(
        "Using PostgreSQL database %r at %s:%s",
        _db.get("NAME"),
        _db.get("HOST"),
        _db.get("PORT"),
    )
elif "sqlite" in _engine:
    logger.info("Using SQLite database %s", _db.get("NAME"))
