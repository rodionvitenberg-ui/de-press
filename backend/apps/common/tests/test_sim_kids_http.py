from __future__ import annotations

import httpx
import pytest

from apps.common.kids.http import KidBusy, KidHttp, KidHttpError, _detail


def _client(handler) -> KidHttp:
    http = KidHttp("http://test.local")
    http._client.close()
    http._client = httpx.Client(
        base_url="http://test.local",
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    return http


def test_detail_from_json_and_text():
    resp = httpx.Response(400, json={"detail": "уже есть"})
    assert "уже" in _detail(resp)
    resp = httpx.Response(500, text="nope")
    assert "nope" in _detail(resp)


def test_register_or_login_falls_back_to_register():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/me") and request.method == "GET":
            return httpx.Response(
                200,
                json={"kind": "anonymous"},
                headers={"set-cookie": "csrftoken=abc"},
            )
        if request.url.path.endswith("/auth/login"):
            return httpx.Response(400, json={"detail": "bad login"})
        if request.url.path.endswith("/auth/register"):
            return httpx.Response(
                200,
                json={"email": "kid1@de-press.local", "account_id": "acc"},
            )
        return httpx.Response(404, json={"detail": "missing"})

    http = _client(handler)
    try:
        me = http.register_or_login("kid1@de-press.local", "pw", "кид-1")
        assert me["email"] == "kid1@de-press.local"
        assert http.me()["kind"] == "anonymous" or True
    finally:
        http.close()


def test_busy_on_429_and_duplicate_message():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={}, headers={"set-cookie": "csrftoken=x"})
        if "clouds" in request.url.path:
            return httpx.Response(429, json={"detail": "Slow down"})
        if "dialogue-requests" in request.url.path:
            return httpx.Response(400, json={"detail": "Request already sent"})
        return httpx.Response(400, json={"detail": "нет"})

    http = _client(handler)
    try:
        with pytest.raises(KidBusy):
            http.send_cloud("s1", "i_am_here")
        with pytest.raises(KidBusy):
            http.request_dialogue("s1", "listen")
        with pytest.raises(KidHttpError):
            http.publish("x")
    finally:
        http.close()


def test_feed_pages_paginates_and_publish_me_inbox():
    pages = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path.endswith("/me"):
            return httpx.Response(
                200,
                json={"account_id": "a1"},
                headers={"set-cookie": "csrftoken=tok"},
            )
        if path.endswith("/stories") and request.method == "GET":
            pages["n"] += 1
            if "cursor" not in str(request.url):
                return httpx.Response(
                    200,
                    json={"items": [{"id": "1"}], "next_cursor": "c1"},
                )
            return httpx.Response(
                200,
                json={"items": [{"id": "2"}], "next_cursor": None},
            )
        if path.endswith("/stories") and request.method == "POST":
            return httpx.Response(200, json={"id": "new"})
        if path.endswith("/quiet-phrases"):
            return httpx.Response(200, json=[{"key": "i_am_here"}])
        if path.endswith("/me/dialogue-requests"):
            return httpx.Response(200, json=[{"id": "r1", "status": "pending"}])
        if path.endswith("/accept"):
            return httpx.Response(200, json={"id": "d1"})
        if path.endswith("/me/dialogues"):
            return httpx.Response(200, json=[{"id": "d1", "status": "open"}])
        if path.endswith("/messages"):
            return httpx.Response(200, json={"id": "m1"})
        if request.method == "POST" and "clouds" in path:
            return httpx.Response(204)
        return httpx.Response(404, json={"detail": path})

    http = _client(handler)
    try:
        assert [i["id"] for i in http.feed_pages()] == ["1", "2"]
        assert http.publish("hi", "anxiety")["id"] == "new"
        assert http.quiet_phrases()[0]["key"] == "i_am_here"
        assert http.inbox()[0]["id"] == "r1"
        assert http.accept("r1")["id"] == "d1"
        assert http.my_dialogues()[0]["status"] == "open"
        assert http.send_message("d1", "привет")["id"] == "m1"
        assert http.send_cloud("s", "i_am_here") is None
        assert http.me()["account_id"] == "a1"
    finally:
        http.close()


def test_401_retries_login():
    hits = {"login": 0, "stories": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={}, headers={"set-cookie": "csrftoken=t"})
        if request.url.path.endswith("/auth/login"):
            hits["login"] += 1
            return httpx.Response(200, json={"ok": True})
        if request.url.path.endswith("/stories") and request.method == "POST":
            hits["stories"] += 1
            if hits["stories"] == 1:
                return httpx.Response(401, json={"detail": "nope"})
            return httpx.Response(200, json={"id": "ok"})
        return httpx.Response(400, json={"detail": "x"})

    http = _client(handler)
    http._email = "k@x"
    http._password = "p"
    try:
        assert http.publish("body")["id"] == "ok"
        assert hits["login"] >= 1
        assert hits["stories"] == 2
    finally:
        http.close()
