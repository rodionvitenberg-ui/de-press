# PRIVACY.md — what we store and what we don't

de-press.co is a non-profit platform of quiet support. Anonymity here is not a
statement but a system property: it can be verified from the code. This
document is a factual inventory of the backend data (code references included).

## Principles

1. **Anon-first.** No feature requires registration. Email and Telegram are
   optional notification channels, not the default sign-in
   (`backend/apps/identity/models.py`: `Account` — "Optional registered identity").
2. **Data minimization.** No real names, phone numbers, birth dates,
   geolocation, avatars, social graph. The pseudonym is a free-form string,
   entered optionally.
3. **No tracking.** The app code contains no analytics, pixels, ads,
   fingerprinting, or engagement metrics. Public like-counters do not exist
   by product design (quiet empathy instead of virality).
4. **ZK patterns stay on the device.** Client-side behavioral self-help
   patterns live in the browser's IndexedDB and are never sent to the server.

## What we store (and why)

| Data | Where | Why | Identity link |
|---|---|---|---|
| Pseudonym, helper duty flags, org | `Account` | help-track bookkeeping | optional account (email+password) |
| Email | `Account.email` | only if the user created an account | optional |
| Telegram id/username | `Account.telegram_id` | only sign-in via the TG Mini App (ADR-0013) | optional |
| Anonymous session: UUID, pseudonym | `AnonymousSession` | cookie identity without registration | pseudonymous |
| Contact email | `AnonymousSession.contact_email` | magic-link for notifications, optional | optional |
| Monologues, dialogues, messages | `Story`, `Dialogue`, `Message` | the product itself | author = session/account UUID, never a name |
| Voice notes, video circles | files under `media/` | dialogues, with the author's consent | deleted: see retention |
| Notifications | `Notification` | private events of the recipient | payload = id references only |
| Digests | `EmailDigest` | opt-in email notifications | the address exists only for delivery |
| Reports, blocks | `Report`, `Block` | moderation by complaint | pseudonymous |
| Public Solana tip address | `Account.tip_wallet_address` | opt-in "thank a helper" (ADR-0020) | published by the helper themselves |
| Duty intervals | `DutySegment` | transparent fund report (ADR-0020) | links to an account; the report shows a pseudonym |
| Therapist profile: pseudonym, approach, languages, rate, public Solana address | `TherapistProfile` | therapy catalog (ADR-0022) | published by the therapist themselves; admin invite required |
| Therapy session: status, price, client pseudonym, dialogue refs | `TherapySession` | payment statuses and the session channel | payment is a direct wallet → wallet transfer; the platform stores only the status and the rate amount |

## What we do NOT store

- **IP addresses.** The app code never writes an IP anywhere. The only use is
  a rate limit for the translation catalog of session-less requests: Redis
  holds only a `SECRET_KEY`-salted SHA-256 hash with a 1-hour TTL
  (`backend/api/v1/i18n.py`, `_rate_key`). Even the raw IP never appears in
  the cache.
- **User-Agent.** Never read, never written.
- **Access logs with IPs.** Nginx in production uses a privacy format without
  IP or UA (`deploy/nginx-de-press.conf.template`, `log_format privacy`).
- **Behavioral analytics.** No Google Analytics / Yandex.Metrica / Sentry
  profiles.
- **Self-support patterns.** ZK patterns never leave the device.
- **Public metrics.** Likes/views do not exist in the data model.
- **Keys and payments.** The platform never holds private keys, never executes
  transactions, and runs no RPC nodes: money moves only wallet → wallet, the
  treasury is a public Squads multisig (ADR-0020). Therapy payment is a
  direct client → therapist transfer; the therapist confirms receipt
  themselves, the platform sees no transactions and is not an arbiter
  (ADR-0022).

## Retention

- Voice messages: `delete_on_close` by default — deleted when the dialogue
  closes (`VoiceRetention`); "keep" is an explicit author choice.
- Video circles: deleted when the dialogue closes.
- Sessions: an anon session lives in the user's cookie; the server knows
  nothing about the human behind it except the UUID and the optional fields
  from the table above.

## Verifiability

Everything above is a property of the code, not a promise: models —
`backend/apps/*/models.py`, middleware — `backend/apps/identity/middleware.py`
(cookie only, no logs), rate limit — `backend/api/v1/i18n.py`, nginx —
`deploy/nginx-de-press.conf.template`, fund — `backend/apps/fund/` (ADR-0020), therapy
— `backend/apps/therapy/` (ADR-0022).
The platform is self-hostable: anyone can run their own instance per
`de-press-docs/app/DEPLOY.md` (systemd) or the root `docker-compose.yml`
(docker) and inspect the DB tables themselves.
