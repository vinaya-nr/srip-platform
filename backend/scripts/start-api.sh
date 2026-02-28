#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec gunicorn -k uvicorn.workers.UvicornWorker -w "${GUNICORN_WORKERS:-4}" -b 0.0.0.0:8000 app.main:app
