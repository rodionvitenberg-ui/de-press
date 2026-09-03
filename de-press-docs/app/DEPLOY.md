# DEPLOY — staging/prod on a single VPS (systemd + nginx, no docker)

> Alternative self-host path: **Docker Compose** — see the root `docker-compose.yml`
> and the *Quick start (docker)* section of the README. This runbook is the bare-VPS
> systemd path.

The scheme: one origin `https://app.depress.co` (replace with your domain). nginx serves
the static files (the browser SPA — `/`, the Telegram Mini App — `/tg/`, the staff admin
console — `/console/`, the Django admin — `/admin/`, the static — `/static/`,
the media — `/media/`) and proxies `/api` `/admin` `/docs` `/openapi.json` `/ws` to
daphne `127.0.0.1:8000`. Postgres and Redis — system packages. The Celery worker + beat —
systemd units. The backups — a systemd timer (`pg_dump -Fc`, a 14-day retention).

The `deploy/` directory contains **templates** only: `deploy/*.template` (nginx site,
the systemd units and the backup timer) plus `deploy/render.sh`, which renders them
into concrete files from your env values (see `deploy/depress.env.example`). The app
env template — `.env.prod.example` at the root.

## 1. The server (Ubuntu 24.04)

```bash
sudo apt update && sudo apt install -y nginx postgresql redis-server python3-venv git
sudo useradd -r -m -d /opt/de-press -s /bin/bash depress
sudo mkdir -p /etc/depress /var/backups/depress && sudo chown postgres /var/backups/depress
```

## 2. Postgres

```bash
sudo -u postgres psql -c "CREATE ROLE depress LOGIN PASSWORD '<password>';"
sudo -u postgres createdb -O depress depress
```

## 3. The code + venv

```bash
sudo -u depress git clone <repo-url> /opt/de-press
cd /opt/de-press/backend && sudo -u depress python3 -m venv .venv
sudo -u depress .venv/bin/pip install -r requirements/production.txt
```

## 4. Env

```bash
sudo cp .env.prod.example /etc/depress/depress.env
sudo chmod 600 /etc/depress/depress.env && sudoedit /etc/depress/depress.env
```

Fill in mandatory: `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, the domain in
`DJANGO_ALLOWED_HOSTS`/`DJANGO_CORS_ALLOWED_ORIGINS`/`PUBLIC_BASE_URL`.
The rest is optional (AI/translator/Telegram — empty = offline modes).

Append the ops values used by `render.sh` (step 6/8): `DEPRESS_DOMAIN=app.depress.co`
and the rest from `deploy/depress.env.example` (paths, user, api port, backup dir).
The app ignores unknown keys, so one env file is enough.

## 5. Migrations, static, seed

```bash
sudo -u depress bash -c 'cd /opt/de-press/backend && set -a && . /etc/depress/depress.env && set +a && \\
  DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py migrate && \\
  DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py collectstatic --noinput && \\
  DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py seed_quiet_phrases && \\
  DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py createsuperuser'
```

## 6. The systemd units

```bash
sudo -u depress bash deploy/render.sh /etc/depress/depress.env
sudo cp deploy/depress-api.service deploy/depress-celery.service \
        deploy/depress-celery-beat.service deploy/depress-backup.service \
        deploy/depress-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now depress-api depress-celery depress-celery-beat depress-backup.timer
```

## 7. The frontends (build locally, no node is needed on the server)

```bash
cd apps/browser && npm ci && npx vite build
cd ../mini-app && npm ci && npx vite build   # base=/tg/
cd ../admin && npm ci && npx vite build      # base=/console/
rsync -a --delete apps/browser/dist/  deploy@app.depress.co:/opt/de-press/apps/browser/dist/
rsync -a --delete apps/mini-app/dist/ deploy@app.depress.co:/opt/de-press/apps/mini-app/dist/
rsync -a --delete apps/admin/dist/    deploy@app.depress.co:/opt/de-press/apps/admin/dist/
```

Note: the staff admin console (the new Vite app `apps/admin`) is served from
`/console/` on the same origin — the code never ships to regular users, and every
API under `/api/v1/admin/*` requires a staff session (403 otherwise). The Django
admin stays at `/admin/` as the fallback tool.

## 8. nginx + TLS

```bash
# render.sh (step 6) already produced deploy/nginx-de-press.conf from the template
sudo cp deploy/nginx-de-press.conf /etc/nginx/sites-available/de-press
sudo ln -sf /etc/nginx/sites-available/de-press /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo apt install -y certbot python3-certbot-nginx && sudo certbot --nginx -d <your-domain>
```

## 8.1 coturn — TURN/STUN for the live voice (ADR 0021)

The live 1:1 call in the dialogue goes P2P; coturn is needed only for strict NATs.

```bash
sudo apt install -y coturn
sudo systemctl enable --now coturn   # older packages: TURNSERVER_ENABLED=1 in /etc/default/coturn
```

A minimal `/etc/turnserver.conf` (substitute your values):

```
listening-port=3478
fingerprint
lt-cred-mech
user=<login>:<password>
realm=<your-domain>
external-ip=<public-IP>   # only if the VPS is behind the provider's NAT
min-port=49152
max-port=65535
no-cli
```

Open the ports: `3478/udp+tcp` and `49152-65535/udp` (the relay range), then
restart: `sudo systemctl restart coturn`. In `/etc/depress/depress.env`:

```
WEBRTC_TURN_URL=turn:<your-domain-or-IP>:3478?transport=udp
WEBRTC_TURN_USERNAME=<login>
WEBRTC_TURN_CREDENTIAL=<password>
```

Check: `curl https://<your-domain>/api/v1/rtc/config` → `ice_servers`
non-empty. Empty variables = ICE over direct candidates only (LAN,
perceptual NAT) — the call may not connect on mobile networks.

## 9. The Telegram Mini App

BotFather → the Menu Button URL `https://<your-domain>/tg/`; `TELEGRAM_BOT_TOKEN` /
`TELEGRAM_BOT_USERNAME` — into `/etc/depress/depress.env` (initData authentication).

## 10. Updating (rollout)

```bash
cd /opt/de-press && sudo -u depress git pull
cd backend && sudo -u depress .venv/bin/pip install -r requirements/production.txt
# step 5 (migrate + collectstatic), then:
sudo systemctl restart depress-api depress-celery depress-celery-beat
# the frontends: build locally and rsync (step 7); sw.js is updated by the new browser build
```

## 11. Backups and restore

Daily at 04:00 the timer puts `/var/backups/depress/depress-YYYY-MM-DD.dump`
(`pg_dump -Fc`); older than 14 days — deleted. Restore:

```bash
sudo -u postgres pg_restore -d depress --clean /var/backups/depress/<file>.dump
```

## 12. The post-deploy check

```bash
curl https://<your-domain>/api/v1/health    # {"status":"ok","database":true,...}
BASE_URL=https://<your-domain> bash scripts/smoke_api.sh
journalctl -u depress-api -f              # when troubleshooting
```

Notes: `config.settings.production` enables `DEBUG=false` and Secure cookies —
the site is https-only; `/admin` requires `collectstatic` (step 5); the manual
pilot checklist after the deploy — [`PILOT.md`](./PILOT.md).
