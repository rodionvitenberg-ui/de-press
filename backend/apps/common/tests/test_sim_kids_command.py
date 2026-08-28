from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


def test_sim_kids_blocked_without_debug(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError, match="laptop client"):
        call_command("sim_kids", n=3)


def test_sim_kids_rejects_bad_n(settings):
    settings.DEBUG = True
    with pytest.raises(CommandError, match="--n"):
        call_command("sim_kids", n=2)


def test_sim_kids_invokes_runner(monkeypatch, settings):
    settings.DEBUG = True
    called: dict = {}

    def fake_run(*, n, api_origin, log):
        called["n"] = n
        called["api"] = api_origin
        log("hi")

    monkeypatch.setattr(
        "apps.common.management.commands.sim_kids.run_kids",
        fake_run,
    )
    call_command("sim_kids", n=3, api="http://127.0.0.1:9")
    assert called == {"n": 3, "api": "http://127.0.0.1:9"}


def test_sim_kids_allows_flag_when_not_debug(monkeypatch, settings):
    settings.DEBUG = False
    called = {"ok": False}

    def fake_run(**kwargs):
        called["ok"] = True

    monkeypatch.setattr(
        "apps.common.management.commands.sim_kids.run_kids",
        fake_run,
    )
    call_command("sim_kids", n=4, i_know_this_is_local=True)
    assert called["ok"] is True
