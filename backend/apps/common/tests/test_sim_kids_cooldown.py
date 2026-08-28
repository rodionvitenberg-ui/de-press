from __future__ import annotations

import random

from apps.common.kids.cooldown import (
    backoff_on_error,
    new_story_delay,
    pick_action,
    stagger_delay,
)


def test_stagger():
    assert stagger_delay(0) == 0
    assert stagger_delay(3) == 21


def test_new_story_delay_spread():
    delays = {new_story_delay(i, "story-1") for i in range(4)}
    assert all(0 <= d < 90 for d in delays)
    assert len(delays) >= 2


def test_pick_action_weights():
    rng = random.Random(0)
    counts = {k: 0 for k in ("cloud", "request", "chat", "publish")}
    for _ in range(10_000):
        counts[pick_action(rng)] += 1
    assert counts["cloud"] > counts["publish"] * 5


def test_backoff_caps_at_10_min():
    assert backoff_on_error(400.0) == 600.0


def test_cooldown_range_keys():
    from apps.common.kids.cooldown import cooldown_range

    lo, hi = cooldown_range("cloud")
    assert lo == 25
    assert hi == 45
