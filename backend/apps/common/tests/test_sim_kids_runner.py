from __future__ import annotations

import threading
import time

from apps.common.kids import runner as runner_mod
from apps.common.kids.http import KidBusy


class FakeHttp:
    def __init__(self, origin):
        self.origin = origin
        self.clouds: list[tuple[str, str]] = []
        self.accepted: list[str] = []
        self.closed = False

    def register_or_login(self, *args, **kwargs):
        return {"email": args[0]}

    def me(self):
        return {"account_id": "11111111-1111-1111-1111-111111111111"}

    def quiet_phrases(self):
        return [{"key": "i_am_here"}]

    def inbox(self):
        return [{"id": "req-1", "status": "pending"}]

    def accept(self, request_id):
        self.accepted.append(request_id)
        return {"id": "d1"}

    def feed_pages(self, **kwargs):
        return [{"id": "story-1", "author_key": "a:other"}]

    def send_cloud(self, story_id, phrase_key):
        self.clouds.append((story_id, phrase_key))
        return {}

    def request_dialogue(self, *args, **kwargs):
        return {}

    def my_dialogues(self):
        return []

    def publish(self, *args, **kwargs):
        return {}

    def send_message(self, *args, **kwargs):
        return {}

    def close(self):
        self.closed = True


def test_preview_trims():
    assert runner_mod._preview("  a   b  " * 20).startswith("a b")
    assert len(runner_mod._preview("x" * 80)) == 40


def test_kid_loop_cloud_and_accept(monkeypatch):
    fake = FakeHttp("http://x")

    def factory(origin):
        return fake

    monkeypatch.setattr(runner_mod, "KidHttp", factory)
    monkeypatch.setattr(runner_mod, "stagger_delay", lambda i: 0)
    monkeypatch.setattr(runner_mod, "new_story_delay", lambda *a: 0)
    monkeypatch.setattr(runner_mod, "pick_action", lambda rng: "cloud")
    monkeypatch.setattr(runner_mod, "complete", lambda *a, **k: "текст")

    stop = threading.Event()
    logs: list[str] = []
    t = threading.Thread(
        target=runner_mod._kid_loop,
        args=(0, stop, "http://x", "pw", logs.append),
        daemon=True,
    )
    t.start()
    deadline = time.time() + 3
    while time.time() < deadline and not fake.clouds:
        time.sleep(0.05)
    stop.set()
    t.join(timeout=2)
    assert fake.accepted == ["req-1"]
    assert fake.clouds
    assert fake.closed is True
    assert any("online" in m for m in logs)


def test_kid_loop_busy_backoff(monkeypatch):
    class BusyHttp(FakeHttp):
        def send_cloud(self, story_id, phrase_key):
            raise KidBusy("подожди")

    fake = BusyHttp("http://x")
    monkeypatch.setattr(runner_mod, "KidHttp", lambda origin: fake)
    monkeypatch.setattr(runner_mod, "stagger_delay", lambda i: 0)
    monkeypatch.setattr(runner_mod, "new_story_delay", lambda *a: 0)
    monkeypatch.setattr(runner_mod, "pick_action", lambda rng: "cloud")
    stop = threading.Event()
    logs: list[str] = []
    t = threading.Thread(
        target=runner_mod._kid_loop,
        args=(0, stop, "http://x", "pw", logs.append),
        daemon=True,
    )
    t.start()
    deadline = time.time() + 3
    while time.time() < deadline and not any("busy" in m for m in logs):
        time.sleep(0.05)
    stop.set()
    t.join(timeout=2)
    assert any("busy" in m for m in logs)


def _run_action(monkeypatch, fake, action: str) -> list[str]:
    monkeypatch.setattr(runner_mod, "KidHttp", lambda origin: fake)
    monkeypatch.setattr(runner_mod, "stagger_delay", lambda i: 0)
    monkeypatch.setattr(runner_mod, "new_story_delay", lambda *a: 0)
    monkeypatch.setattr(runner_mod, "pick_action", lambda rng: action)
    monkeypatch.setattr(runner_mod, "complete", lambda *a, **k: "реплика")
    stop = threading.Event()
    logs: list[str] = []
    t = threading.Thread(
        target=runner_mod._kid_loop,
        args=(0, stop, "http://x", "pw", logs.append),
        daemon=True,
    )
    t.start()
    deadline = time.time() + 3
    while time.time() < deadline and not any(
        action.split("_")[0] in m for m in logs if m.startswith("kid-")
    ):
        time.sleep(0.05)
    stop.set()
    t.join(timeout=2)
    return logs


def test_kid_loop_request_chat_publish(monkeypatch):
    class RichHttp(FakeHttp):
        def my_dialogues(self):
            return [{"id": "d1", "status": "open", "peer_key": "a:human"}]

        def request_dialogue(self, story_id, intent, note=""):
            self.requested = (story_id, intent, note)
            return {}

        def send_message(self, dialogue_id, body):
            self.sent = (dialogue_id, body)
            return {}

        def publish(self, body, topic=None):
            self.posted = (body, topic)
            return {}

    fake = RichHttp("http://x")
    logs = _run_action(monkeypatch, fake, "request")
    assert any("request" in m for m in logs)
    assert fake.requested[0] == "story-1"

    fake = RichHttp("http://x")
    logs = _run_action(monkeypatch, fake, "chat")
    assert any("chat" in m for m in logs)
    assert fake.sent == ("d1", "реплика")

    fake = RichHttp("http://x")
    logs = _run_action(monkeypatch, fake, "publish")
    assert any("publish" in m for m in logs)
    assert fake.posted[0] == "реплика"


def test_skips_sibling_request_chat_and_accept(monkeypatch):
    class Spy(FakeHttp):
        def __init__(self, origin):
            super().__init__(origin)
            self.requested = None
            self.sent = None

        def inbox(self):
            return [{"id": "req-sib", "status": "pending", "from_key": "a:sibling"}]

        def feed_pages(self, **kwargs):
            return [{"id": "story-1", "author_key": "a:sibling"}]

        def my_dialogues(self):
            return [{"id": "d1", "status": "open", "peer_key": "a:sibling"}]

        def request_dialogue(self, *args, **kwargs):
            self.requested = args
            return {}

        def send_message(self, *args, **kwargs):
            self.sent = args
            return {}

    fake = Spy("http://x")
    monkeypatch.setattr(runner_mod, "KidHttp", lambda origin: fake)
    monkeypatch.setattr(runner_mod, "stagger_delay", lambda i: 0)
    monkeypatch.setattr(runner_mod, "new_story_delay", lambda *a: 0)
    monkeypatch.setattr(runner_mod, "pick_action", lambda rng: "request")
    monkeypatch.setattr(runner_mod, "complete", lambda *a, **k: "реплика")
    stop = threading.Event()
    t = threading.Thread(
        target=runner_mod._kid_loop,
        args=(0, stop, "http://x", "pw", lambda m: None, {"a:sibling"}),
        daemon=True,
    )
    t.start()
    time.sleep(0.5)
    stop.set()
    t.join(timeout=2)
    assert fake.requested is None
    assert fake.sent is None
    assert fake.accepted == []


def test_chats_only_with_human_peer(monkeypatch):
    class Spy(FakeHttp):
        def my_dialogues(self):
            return [
                {"id": "kid-chat", "status": "open", "peer_key": "a:sibling"},
                {"id": "human-chat", "status": "open", "peer_key": "a:human"},
            ]

        def send_message(self, dialogue_id, body):
            self.sent = (dialogue_id, body)
            return {}

    fake = Spy("http://x")
    monkeypatch.setattr(runner_mod, "KidHttp", lambda origin: fake)
    monkeypatch.setattr(runner_mod, "stagger_delay", lambda i: 0)
    monkeypatch.setattr(runner_mod, "pick_action", lambda rng: "chat")
    monkeypatch.setattr(runner_mod, "complete", lambda *a, **k: "реплика")
    stop = threading.Event()
    logs: list[str] = []
    t = threading.Thread(
        target=runner_mod._kid_loop,
        args=(0, stop, "http://x", "pw", logs.append, {"a:sibling"}),
        daemon=True,
    )
    t.start()
    deadline = time.time() + 3
    while time.time() < deadline and not getattr(fake, "sent", None):
        time.sleep(0.05)
    stop.set()
    t.join(timeout=2)
    assert fake.sent == ("human-chat", "реплика")
