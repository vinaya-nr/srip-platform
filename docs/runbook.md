# SRIP Backend Runbook

## Core Commands

- Start stack: `docker compose up --build`
- Run migrations: `docker compose exec api alembic upgrade head`
- API logs: `docker compose logs -f api`
- Worker logs: `docker compose logs -f worker`
- Beat logs: `docker compose logs -f beat`
- Deploy prod overlay: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`

## Operational Checks

- Health endpoint: `GET /api/v1/health`
- Metrics endpoint: `GET /metrics`
- Redis streams:
  - `srip:sales:events`
  - `srip:inventory:events`

## Incident Triage

- Use `X-Correlation-ID` from API response headers.
- Search logs by `correlation_id` to trace request path across API and workers.

## Recovery

- Stop writes: scale API to 0 or put maintenance mode at Nginx.
- Restore latest backup with `scripts/restore_postgres.sh`.
- Run `alembic upgrade head` to verify schema consistency.
- Bring API/worker/beat back and validate `/api/v1/health`.
