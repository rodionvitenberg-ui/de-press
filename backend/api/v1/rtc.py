"""Public RTC config for live 1:1 voice (ADR 0021).

Exposes only the self-hosted ICE servers (coturn). The static TURN
credentials are semi-public by design — see the ADR for the tradeoff.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from django.conf import settings
from ninja import Router, Schema

router = Router(tags=["rtc"])


class RtcConfigOut(Schema):
    ice_servers: list[dict] = []


@router.get("/rtc/config", response=RtcConfigOut)
def rtc_config(request):
    """ICE servers for WebRTC calls. Empty list = direct candidates only."""
    turn = (settings.WEBRTC_TURN_URL or "").strip()
    if not turn:
        return RtcConfigOut(ice_servers=[])
    urls = [turn]
    # STUN on the same coturn host: accept "turn:host:port", "turns://…", bare host.
    parsed = urlsplit(turn)
    host = (
        parsed.hostname
        or (parsed.netloc or parsed.path).split(":")[0]
    ).strip()
    if host:
        urls.append(f"stun:{host}")
    server: dict = {"urls": urls}
    username = (settings.WEBRTC_TURN_USERNAME or "").strip()
    credential = (settings.WEBRTC_TURN_CREDENTIAL or "").strip()
    if username:
        server["username"] = username
    if credential:
        server["credential"] = credential
    return RtcConfigOut(ice_servers=[server])
