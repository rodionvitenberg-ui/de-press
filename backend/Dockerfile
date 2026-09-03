# de-press backend image (daphne ASGI + celery worker/beat share it).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/backend

# Install python deps first (better layer caching).
COPY requirements/ ./requirements/
RUN pip install --upgrade pip \
    && pip install -r requirements/production.txt

COPY . .
RUN mkdir -p media staticfiles

EXPOSE 8005

# Runs `manage.py migrate` (+ `seed_local` when SEED=1) before the command.
ENTRYPOINT ["/srv/backend/docker-entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8005", "config.asgi:application"]
