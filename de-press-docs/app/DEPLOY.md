# DEPLOY — staging/prod на одном VPS (systemd + nginx, без docker)

Схема: один origin `https://app.depress.co` (замените на свой домен). nginx раздаёт
статику (browser SPA — `/`, Telegram Mini App — `/tg/`, статика админки — `/static/`,
медиа — `/media/`) и проксирует `/api` `/admin` `/docs` `/openapi.json` `/ws` на
daphne `127.0.0.1:8000`. Postgres и Redis — системные пакеты. Celery worker + beat —
systemd-юниты. Бэкапы — systemd timer (`pg_dump -Fc`, retention 14 дней).

Артефакты в `deploy/` репозитория: `depress-api.service`, `depress-celery.service`,
`depress-celery-beat.service`, `depress-backup.service` + `depress-backup.timer`,
`nginx-de-press.conf`; env-шаблон — `.env.prod.example` в корне.

## 1. Сервер (Ubuntu 24.04)

```bash
sudo apt update && sudo apt install -y nginx postgresql redis-server python3-venv git
sudo useradd -r -m -d /opt/de-press -s /bin/bash depress
sudo mkdir -p /etc/depress /var/backups/depress && sudo chown postgres /var/backups/depress
```

## 2. Postgres

```bash
sudo -u postgres psql -c "CREATE ROLE depress LOGIN PASSWORD '<пароль>';"
sudo -u postgres createdb -O depress depress
```

## 3. Код + venv

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

Обязательно заполнить: `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, домен в
`DJANGO_ALLOWED_HOSTS`/`DJANGO_CORS_ALLOWED_ORIGINS`/`PUBLIC_BASE_URL`.
Остальное опционально (AI/translator/Telegram — пусто = оффлайн-режимы).

## 5. Миграции, статика, seed

```bash
sudo -u depress bash -c 'cd /opt/de-press/backend && set -a && . /etc/depress/depress.env && set +a && \
  DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py migrate && \
  DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py collectstatic --noinput && \
  DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py seed_quiet_phrases && \
  DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py createsuperuser'
```

## 6. systemd-юниты

```bash
sudo cp deploy/depress-api.service deploy/depress-celery.service \
        deploy/depress-celery-beat.service deploy/depress-backup.service \
        deploy/depress-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now depress-api depress-celery depress-celery-beat depress-backup.timer
```

## 7. Фронтонты (сборка локально, на сервер node не нужен)

```bash
cd apps/browser && npm ci && npx vite build
cd ../mini-app && npm ci && npx vite build   # base=/tg/
rsync -a --delete apps/browser/dist/  deploy@app.depress.co:/opt/de-press/apps/browser/dist/
rsync -a --delete apps/mini-app/dist/ deploy@app.depress.co:/opt/de-press/apps/mini-app/dist/
```

## 8. nginx + TLS

```bash
sudo cp deploy/nginx-de-press.conf /etc/nginx/sites-available/de-press
sudo sed -i 's/app.depress.co/<ваш-домен>/g' /etc/nginx/sites-available/de-press
sudo ln -sf /etc/nginx/sites-available/de-press /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo apt install -y certbot python3-certbot-nginx && sudo certbot --nginx -d <ваш-домен>
```

## 8.1 coturn — TURN/STUN для живого голоса (ADR 0021)

Живой 1:1 звонок в диалоге идёт P2P; coturn нужен только для строгих NAT.

```bash
sudo apt install -y coturn
sudo systemctl enable --now coturn   # старые пакеты: TURNSERVER_ENABLED=1 в /etc/default/coturn
```

Минимальный `/etc/turnserver.conf` (подставьте свои значения):

```
listening-port=3478
fingerprint
lt-cred-mech
user=<логин>:<пароль>
realm=<ваш-домен>
external-ip=<внешний-IP>   # только если VPS за NAT провайдера
min-port=49152
max-port=65535
no-cli
```

Открыть порты: `3478/udp+tcp` и `49152-65535/udp` (relay-диапазон), затем
перезапустить: `sudo systemctl restart coturn`. В `/etc/depress/depress.env`:

```
WEBRTC_TURN_URL=turn:<ваш-домен-или-IP>:3478?transport=udp
WEBRTC_TURN_USERNAME=<логин>
WEBRTC_TURN_CREDENTIAL=<пароль>
```

Проверка: `curl https://<ваш-домен>/api/v1/rtc/config` → `ice_servers`
непустые. Пустые переменные = ICE только по прямым кандидатам (LAN,
перцептивный NAT) — звонок может не соединиться на мобильных сетях.

## 9. Telegram Mini App

BotFather → Menu Button URL `https://<ваш-домен>/tg/`; `TELEGRAM_BOT_TOKEN` /
`TELEGRAM_BOT_USERNAME` — в `/etc/depress/depress.env` (initData-аутентификация).

## 10. Обновление (rollout)

```bash
cd /opt/de-press && sudo -u depress git pull
cd backend && sudo -u depress .venv/bin/pip install -r requirements/production.txt
# п.5 (migrate + collectstatic), затем:
sudo systemctl restart depress-api depress-celery depress-celery-beat
# фронты: собрать локально и rsync (п.7); sw.js обновится новой сборкой browser
```

## 11. Бэкапы и восстановление

Ежедневно в 04:00 таймер кладёт `/var/backups/depress/depress-YYYY-MM-DD.dump`
(`pg_dump -Fc`), старше 14 дней — удаляются. Восстановление:

```bash
sudo -u postgres pg_restore -d depress --clean /var/backups/depress/<файл>.dump
```

## 12. Проверка после деплоя

```bash
curl https://<ваш-домен>/api/v1/health    # {"status":"ok","database":true,...}
BASE_URL=https://<ваш-домен> bash scripts/smoke_api.sh
journalctl -u depress-api -f              # при проблемах
```

Замечания: `config.settings.production` включает `DEBUG=false` и Secure-cookies —
сайт доступен только по https; `/admin` требует `collectstatic` (п.5); ручной
пилотный чеклист после деплоя — [`PILOT.md`](./PILOT.md).
