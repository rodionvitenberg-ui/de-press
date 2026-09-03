"""Lightweight crisis heuristic — not a diagnostic tool."""

from __future__ import annotations

import re

# Conservative keywords (RU + EN). Prefer false positives over silence.
_CRISIS_PATTERNS = [
    r"\bсуицид",
    r"\bуби(ть|ю)\s+себя",
    r"\bпоконч",
    r"\bне\s+хочу\s+жить",
    r"\bхочу\s+умереть",
    r"\bself[-\s]?harm",
    r"\bsuicid",
    r"\bkill\s+myself",
    r"\bend\s+my\s+life",
    r"\bпорезать\s+себя",
    r"\bсвести\s+сч[её]ты",
    r"\bwant\s+to\s+die",
    r"\bno\s+reason\s+to\s+live",
    r"\bhurt\s+myself",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _CRISIS_PATTERNS]


def looks_like_crisis(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _COMPILED)


CRISIS_REPLY = (
    "I hear that things are very heavy right now — and it matters not to stay alone with this. "
    "If there is risk to yourself: emergency services 112 / 103, a crisis hotline. "
    "You can open the Anti-Panic mode on the site. I am not a replacement for help nearby."
)
