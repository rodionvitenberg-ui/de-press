# System Postgres database `depress` is the local primary (Docker optional)

Local development binds Django to the host PostgreSQL database `depress` on `127.0.0.1:5432` via `POSTGRES_*` in the repo `.env`. Docker Compose (`backend/docker-compose.yml`, default host port 5433) stays optional for machines without a system Postgres. SQLite is allowed only for pytest (`DEPRESS_USE_SQLITE=1`), not for Daphne or everyday dev — dual SQLite/Postgres stores caused “empty feed” confusion when the UI was pointed at one store and seeds lived in the other.

**Considered options:** Docker-only Postgres on 5433; SQLite for all local work. Rejected: Docker is not required for this project’s daily loop; SQLite diverges from prod and from the already-existing `depress` database.
