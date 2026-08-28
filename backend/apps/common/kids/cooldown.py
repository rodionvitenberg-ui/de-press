"""Action weights and pauses for local sim_kids."""

from __future__ import annotations

import hashlib
import random
from typing import Literal

Action = Literal["cloud", "request", "chat", "publish"]

ACTIONS: tuple[Action, ...] = ("cloud", "request", "chat", "publish")

AUTHOR_REQUEST_GAP = 15 * 60

_COOLDOWN_RANGE: dict[str, tuple[float, float]] = {
    "cloud": (25, 45),
    "request": (180, 360),
    "chat_after_peer": (8, 20),
    "chat_idle": (45, 90),
    "publish": (900, 1500),
}


def stagger_delay(kid_index: int) -> float:
    return kid_index * 7.0


def new_story_delay(kid_index: int, story_id: str) -> float:
    digest = hashlib.sha256(f"{kid_index}:{story_id}".encode()).digest()
    return int.from_bytes(digest[:2], "big") % 90


def pick_action(rng: random.Random) -> Action:
    roll = rng.random()
    if roll < 0.55:
        return "cloud"
    if roll < 0.75:
        return "request"
    if roll < 0.95:
        return "chat"
    return "publish"


def cooldown_range(action: str) -> tuple[float, float]:
    return _COOLDOWN_RANGE[action]


def backoff_on_error(prev: float) -> float:
    return min(prev * 2, 600.0)
