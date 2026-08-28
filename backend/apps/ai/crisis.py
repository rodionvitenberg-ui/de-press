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
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _CRISIS_PATTERNS]


def looks_like_crisis(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _COMPILED)


CRISIS_REPLY_RU = (
    "Слышу, что тебе сейчас очень тяжело — и это важно не оставаться с этим одному. "
    "Если есть риск себе: экстренные службы 112 / 103, телефон доверия. "
    "На сайте можно открыть режим Anti-Panic. Я не замена помощи рядом."
)
