"""Threaded sim_kids loops against the public API (laptop client)."""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable

from django.conf import settings

from apps.common.kids.cooldown import (
    AUTHOR_REQUEST_GAP,
    backoff_on_error,
    cooldown_range,
    new_story_delay,
    pick_action,
    stagger_delay,
)
from apps.common.kids.http import KidBusy, KidHttp, KidHttpError
from apps.common.kids.ollama import complete

TOPICS = ("loneliness", "anxiety", "exhaustion", "grief", "other")
INTENTS = ("listen", "share", "advice_ok", "mutual")
LogFn = Callable[[str], None]


def _preview(text: str) -> str:
    compact = " ".join((text or "").split())
    return compact[:40]


def _is_sibling(key: str | None, sibling_keys: set[str], own_key: str) -> bool:
    if not key:
        return False
    if key == own_key:
        return True
    return key in sibling_keys


def _kid_loop(
    index: int,
    stop: threading.Event,
    api_origin: str,
    password: str,
    log: LogFn,
    sibling_keys: set[str] | None = None,
    ready: threading.Barrier | None = None,
) -> None:
    time.sleep(stagger_delay(index))
    email = f"kid{index + 1}@de-press.local"
    label = f"kid-{index + 1}"
    http = KidHttp(api_origin)
    rng = random.Random(index + 17)
    next_action_at = 0.0
    busy_backoff = 25.0
    clouded: set[str] = set()
    requested_stories: set[str] = set()
    requested_authors: dict[str, float] = {}
    seen_stories: dict[str, float] = {}
    keys = sibling_keys if sibling_keys is not None else set()

    try:
        http.register_or_login(email, password, f"кид-{index + 1}")
        me = http.me()
        own_key = f"a:{me.get('account_id')}" if me.get("account_id") else ""
        if own_key:
            keys.add(own_key)
        if ready is not None:
            ready.wait(timeout=60)
        phrases = http.quiet_phrases()
        if not phrases:
            log(f"{label} no quiet phrases on API, clouds skipped")
        log(f"{label} online api={api_origin}")

        while not stop.is_set():
            try:
                for req in http.inbox():
                    if req.get("status") != "pending":
                        continue
                    if _is_sibling(req.get("from_key"), keys, own_key):
                        continue
                    http.accept(req["id"])
                    log(f"{label} accept {str(req['id'])[:8]}")

                now = time.monotonic()
                humans = [
                    s
                    for s in http.feed_pages()
                    if s.get("author_key")
                    and not _is_sibling(s.get("author_key"), keys, own_key)
                ]
                for story in humans:
                    seen_stories.setdefault(str(story["id"]), now)

                human_chats = [
                    d
                    for d in http.my_dialogues()
                    if d.get("status") == "open"
                    and not _is_sibling(d.get("peer_key"), keys, own_key)
                ]

                if now < next_action_at:
                    stop.wait(2)
                    continue

                action = pick_action(rng)
                if human_chats and rng.random() < 0.45:
                    action = "chat"
                did = False
                used_cd = "cloud"

                if action == "cloud" and humans:
                    phrases = http.quiet_phrases() or phrases
                    ready_stories = [
                        s
                        for s in humans
                        if str(s["id"]) not in clouded
                        and now - seen_stories[str(s["id"])]
                        >= new_story_delay(index, str(s["id"]))
                    ]
                    if phrases and ready_stories:
                        story = rng.choice(ready_stories)
                        phrase = rng.choice(phrases)["key"]
                        try:
                            http.send_cloud(str(story["id"]), phrase)
                        except (KidBusy, KidHttpError) as exc:
                            detail = str(exc).lower()
                            if "cloud" in detail:
                                clouded.add(str(story["id"]))
                                log(f"{label} cloud skip {str(story['id'])[:8]}")
                            elif "phrase" in detail:
                                phrases = http.quiet_phrases()
                                log(f"{label} cloud catalog refresh")
                            else:
                                raise
                        else:
                            clouded.add(str(story["id"]))
                            did = True
                            used_cd = "cloud"
                            log(f"{label} cloud story={str(story['id'])[:8]}")

                elif action == "request" and humans:
                    ready_stories = [
                        s
                        for s in humans
                        if str(s["id"]) not in requested_stories
                        and now
                        - requested_authors.get(s.get("author_key") or "", 0)
                        >= AUTHOR_REQUEST_GAP
                    ]
                    if ready_stories:
                        story = rng.choice(ready_stories)
                        note = complete(
                            "Короткая note к запросу диалога. Без советов. Можно пусто.",
                        )
                        try:
                            http.request_dialogue(
                                str(story["id"]), rng.choice(INTENTS), note
                            )
                        except (KidBusy, KidHttpError) as exc:
                            if "already" in str(exc).lower():
                                requested_stories.add(str(story["id"]))
                                log(f"{label} request skip {str(story['id'])[:8]}")
                            else:
                                raise
                        else:
                            requested_stories.add(str(story["id"]))
                            requested_authors[story.get("author_key") or ""] = now
                            did = True
                            used_cd = "request"
                            log(f"{label} request story={str(story['id'])[:8]}")

                elif action == "chat":
                    if human_chats:
                        dialogue = rng.choice(human_chats)
                        text = complete(
                            "Короткая тихая реплика в чат. Без советов и без позитива.",
                        )
                        if text:
                            http.send_message(str(dialogue["id"]), text)
                            did = True
                            used_cd = "chat_idle"
                            log(f"{label} chat {_preview(text)}")

                elif action == "publish":
                    text = complete(
                        "Тихий монолог от первого лица, 1–2 предложения. Без советов.",
                    )
                    if text:
                        http.publish(text, rng.choice(TOPICS))
                        did = True
                        used_cd = "publish"
                        log(f"{label} publish {_preview(text)}")

                if did:
                    lo, hi = cooldown_range(used_cd)
                    next_action_at = now + rng.uniform(lo, hi)
                    busy_backoff = lo
                else:
                    next_action_at = now + rng.uniform(8, 20)
            except KidBusy as exc:
                busy_backoff = backoff_on_error(busy_backoff)
                next_action_at = time.monotonic() + busy_backoff
                log(f"{label} busy {exc}")
            except KidHttpError as exc:
                busy_backoff = backoff_on_error(busy_backoff)
                next_action_at = time.monotonic() + busy_backoff
                log(f"{label} http {exc}")
            except Exception as exc:  # noqa: BLE001 — keep the loop alive
                busy_backoff = backoff_on_error(busy_backoff)
                next_action_at = time.monotonic() + busy_backoff
                log(f"{label} err {exc}")
            stop.wait(2)
    finally:
        http.close()
        log(f"{label} stop")


def run_kids(*, n: int, api_origin: str, log: LogFn) -> None:
    n = max(3, min(n, 4))
    password = str(getattr(settings, "KIDS_PASSWORD", "kid-local-not-secret"))
    stop = threading.Event()
    sibling_keys: set[str] = set()
    ready = threading.Barrier(n)
    threads = [
        threading.Thread(
            target=_kid_loop,
            args=(i, stop, api_origin, password, log, sibling_keys, ready),
            name=f"sim-kid-{i + 1}",
            daemon=True,
        )
        for i in range(n)
    ]
    log(f"sim_kids laptop client → {api_origin}")
    for t in threads:
        t.start()
    try:
        while True:
            time.sleep(0.5)
            if not any(t.is_alive() for t in threads):
                break
    except KeyboardInterrupt:
        log("stopping…")
    stop.set()
    for t in threads:
        t.join(timeout=8)
