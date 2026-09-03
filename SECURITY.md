# Security Policy

de-press handles emotionally sensitive content and is designed around
zero-knowledge promises ([`PRIVACY.md`](./PRIVACY.md)). Treat anything that breaks
those promises — or leaks data, secrets, or session material — as a security issue.

## Supported versions

Only the latest published state of the `main` branch is supported. There is no
backport window.

## Reporting a vulnerability

Please **do not open a public issue** for an unreleased vulnerability.

- Prefer GitHub's private vulnerability reporting: open the **Security** tab of the
  repository → *Report a vulnerability*.
- If that is not available, email the maintainer at rodionvitenberg@gmail.com with
  enough detail to reproduce (affected component, steps, impact). Do not include live
  production data or other people's content in the report.

You can expect an initial acknowledgment within a few days. After triage we will
coordinate a fix, and only publish details once a patch is available or the issue is
determined to be non-security.

## Scope

In scope: the `backend/`, `apps/`, and `packages/` code in this repository and the
deployment artifacts under `deploy/`. Out of scope: `apps/mini-app/vendor/**`
(GPLv3 third-party code — report upstream to [Ajaxy/telegram-tt](https://github.com/Ajaxy/telegram-tt)),
and dependencies (report to their own projects).

## Security-relevant invariants

- No raw PII, IPs, or user-agent strings in logs; no IP-based rate-limit keys that
  persist identity.
- Emotional patterns stay on the device (IndexedDB); the server never receives them.
- No public like/engagement counters or "who heard" lists.
- Secrets (`DJANGO_SECRET_KEY`, bot/API tokens) only via environment files, never in
  the repository. See `.env.example`.
