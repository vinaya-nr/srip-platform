#!/bin/sh
set -e

echo "Pulling latest images and rebuilding services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "Running migrations in API container..."
docker compose exec -T api alembic upgrade head

echo "Deployment complete."
