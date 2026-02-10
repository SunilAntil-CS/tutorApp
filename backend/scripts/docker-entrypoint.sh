#!/bin/sh
# Run migrations then start the app. Use as Docker ENTRYPOINT so tables exist before uvicorn.
set -e
echo "[entrypoint] Running Alembic migrations..."
cd /app
alembic upgrade head
echo "[entrypoint] Migrations done. Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
