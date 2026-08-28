"""Cookie HTTP client that hits the same public API as the browser."""

from __future__ import annotations

from typing import Any

import httpx


class KidBusy(Exception):
    """Rate-limit or duplicate action — back off."""


class KidHttpError(Exception):
    pass


def _detail(resp: httpx.Response) -> str:
    try:
        data = resp.json()
    except Exception:
        return (resp.text or resp.reason_phrase)[:240]
    detail = data.get("detail", data) if isinstance(data, dict) else data
    return str(detail)[:240]


class KidHttp:
    def __init__(self, api_origin: str):
        self._origin = api_origin.rstrip("/")
        self._client = httpx.Client(
            base_url=self._origin,
            follow_redirects=True,
            timeout=30.0,
        )
        self._email = ""
        self._password = ""
        self._pseudonym = ""

    def close(self) -> None:
        self._client.close()

    def _csrf_headers(self) -> dict[str, str]:
        token = self._client.cookies.get("csrftoken", "")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-CSRFToken"] = token
        return headers

    def _ensure_csrf(self) -> None:
        if not self._client.cookies.get("csrftoken"):
            self._client.get("/api/v1/me")

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        self._ensure_csrf()
        resp = self._client.request(
            method,
            path,
            json=json,
            headers=self._csrf_headers() if json is not None or method != "GET" else None,
        )
        if resp.status_code == 401 and retry_auth and self._email:
            self.register_or_login(self._email, self._password, self._pseudonym)
            return self._request(method, path, json=json, retry_auth=False)
        if resp.status_code == 204:
            return None
        if resp.status_code >= 400:
            detail = _detail(resp)
            low = detail.lower()
            if resp.status_code == 429 or "подожди" in low or "уже" in low:
                raise KidBusy(detail)
            raise KidHttpError(f"{resp.status_code} {detail}")
        if not resp.content:
            return None
        return resp.json()

    def register_or_login(self, email: str, password: str, pseudonym: str) -> dict[str, Any]:
        self._email = email
        self._password = password
        self._pseudonym = pseudonym
        self._ensure_csrf()
        try:
            return self._request(
                "POST",
                "/api/v1/auth/login",
                json={"email": email, "password": password},
                retry_auth=False,
            )
        except KidHttpError:
            return self._request(
                "POST",
                "/api/v1/auth/register",
                json={"email": email, "password": password, "pseudonym": pseudonym},
                retry_auth=False,
            )

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/me")

    def feed_pages(self, *, limit_pages: int = 8) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor: str | None = None
        for _ in range(limit_pages):
            path = "/api/v1/stories"
            if cursor:
                path = f"/api/v1/stories?cursor={cursor}"
            page = self._request("GET", path)
            items.extend(page.get("items") or [])
            cursor = page.get("next_cursor")
            if not cursor:
                break
        return items

    def publish(self, body: str, topic: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"body": body, "pseudonym": None, "topic": topic}
        return self._request("POST", "/api/v1/stories", json=payload)

    def quiet_phrases(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/quiet-phrases") or []

    def send_cloud(self, story_id: str, phrase_key: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/stories/{story_id}/clouds",
            json={"phrase_key": phrase_key},
        )

    def request_dialogue(self, story_id: str, intent: str, note: str = "") -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/stories/{story_id}/dialogue-requests",
            json={"intent": intent, "note": note},
        )

    def inbox(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/me/dialogue-requests") or []

    def accept(self, request_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/dialogue-requests/{request_id}/accept",
            json={},
        )

    def my_dialogues(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/me/dialogues") or []

    def send_message(self, dialogue_id: str, body: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/dialogues/{dialogue_id}/messages",
            json={"body": body},
        )
