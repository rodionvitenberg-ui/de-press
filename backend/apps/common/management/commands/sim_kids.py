"""Laptop client: 3–4 local models hit a (possibly remote) public API."""

from __future__ import annotations

import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.common.kids.runner import run_kids


class Command(BaseCommand):
    help = (
        "Run 3–4 kid accounts from this machine against --api. "
        "Ollama stays local; browser/backend may live on a server. "
        "Kids talk to real users only (no kid-to-kid chat). Ctrl+C to stop."
    )

    def add_arguments(self, parser):
        parser.add_argument("--n", type=int, default=4, help="3 or 4 kids")
        parser.add_argument(
            "--api",
            default=os.environ.get("KIDS_API", "http://127.0.0.1:8005"),
            help="API origin (env KIDS_API, default http://127.0.0.1:8005)",
        )
        parser.add_argument(
            "--i-know-this-is-local",
            action="store_true",
            dest="i_know_this_is_local",
            help="Required when this machine has DEBUG=false",
        )

    def handle(self, *args, **options):
        if not (settings.DEBUG or options["i_know_this_is_local"]):
            raise CommandError(
                "sim_kids is a laptop client. "
                "Run with DEBUG or pass --i-know-this-is-local"
            )
        n = options["n"]
        if n not in (3, 4):
            raise CommandError("--n must be 3 or 4")
        api = options["api"]
        self.stdout.write(f"sim_kids n={n} api={api}")

        def log(msg: str) -> None:
            self.stdout.write(msg)

        run_kids(n=n, api_origin=api, log=log)
