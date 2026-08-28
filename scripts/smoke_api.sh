#!/usr/bin/env bash
# HTTP smoke for pilot (no WebSocket).
set -euo pipefail

BASE="${BASE_URL:-http://127.0.0.1:8005}"
COOKIE_JAR="$(mktemp)"
trap 'rm -f "$COOKIE_JAR"' EXIT

echo "== health =="
curl -sf "$BASE/api/v1/health" | head -c 400
echo

echo "== register =="
EMAIL="pilot_$(date +%s)@example.com"
curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"password123\",\"pseudonym\":\"pilot\"}" \
  "$BASE/api/v1/auth/register" | head -c 300
echo

echo "== publish =="
STORY=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"body":"smoke monologue for pilot","topic":"anxiety"}' \
  "$BASE/api/v1/stories")
echo "$STORY" | head -c 400
echo
SID=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['id'])" "$STORY")

echo "== feed =="
curl -sf "$BASE/api/v1/stories?topic=anxiety" | head -c 200
echo

echo "== empathy (as second visitor) =="
COOKIE_HEARER="$(mktemp)"
curl -sf -c "$COOKIE_HEARER" -b "$COOKIE_HEARER" "$BASE/api/v1/me" >/dev/null
curl -sf -c "$COOKIE_HEARER" -b "$COOKIE_HEARER" -X POST \
  "$BASE/api/v1/stories/$SID/empathy"
echo
curl -sf -c "$COOKIE_HEARER" -b "$COOKIE_HEARER" -X POST \
  "$BASE/api/v1/stories/$SID/empathy"
echo

echo "== hearers (author) =="
HEARERS=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" "$BASE/api/v1/stories/$SID/hearers")
echo "$HEARERS" | head -c 400
echo
HREF=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d[0]['hearer_ref'] if d else '')" "$HEARERS")
if [ -n "$HREF" ]; then
  echo "== outreach one =="
  curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
    -H 'Content-Type: application/json' \
    -d "{\"mode\":\"one\",\"hearer_refs\":[\"$HREF\"],\"intent\":\"listen\"}" \
    "$BASE/api/v1/stories/$SID/outreach" | head -c 400
  echo
fi
rm -f "$COOKIE_HEARER"

echo "== report =="
curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -d '{"reason":"spam","details":"smoke"}' \
  "$BASE/api/v1/stories/$SID/report"
echo

echo "== me stories (pulse) =="
curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" "$BASE/api/v1/me/stories" | head -c 400
echo

echo "== quiet phrases =="
PHRASES=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" "$BASE/api/v1/quiet-phrases")
echo "$PHRASES" | head -c 300
echo
PKEY=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d[0]['key'] if d else '')" "$PHRASES")
COOKIE2="$(mktemp)"
curl -sf -c "$COOKIE2" -b "$COOKIE2" "$BASE/api/v1/me" >/dev/null
if [ -n "$PKEY" ]; then
  curl -sf -c "$COOKIE2" -b "$COOKIE2" \
    -H 'Content-Type: application/json' \
    -d "{\"phrase_key\":\"$PKEY\"}" \
    "$BASE/api/v1/stories/$SID/clouds"
  echo
else
  echo "(no phrases seeded — run: python manage.py seed_quiet_phrases)"
fi

echo "== moderated free-text (pending) =="
curl -sf -c "$COOKIE2" -b "$COOKIE2" \
  -H 'Content-Type: application/json' \
  -d '{"body":"smoke free-text cloud for moderation"}' \
  "$BASE/api/v1/stories/$SID/clouds"
echo

echo "== author clouds (delivered only) =="
curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" "$BASE/api/v1/stories/$SID/clouds" | head -c 400
echo
rm -f "$COOKIE2"

echo "== notifications unread-count (author) =="
CUR=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" "$BASE/api/v1/me/notifications/unread-count")
echo "$CUR" | head -c 200
echo
NID=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('count',0))" "$CUR")
if [ "$NID" -gt 0 ]; then
  echo "== notifications list (first) =="
  FIRST=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" "$BASE/api/v1/me/notifications?limit=1" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['id'] if d else '')")
  if [ -n "$FIRST" ]; then
    echo "== mark one read =="
    curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X POST \
      "$BASE/api/v1/me/notifications/$FIRST/read" | head -c 200
    echo
  fi
fi

echo "OK smoke_api finished (story=$SID email=$EMAIL)"
