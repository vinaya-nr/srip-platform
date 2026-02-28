# Deployment Operations

## Environment

- Development template: `backend/.env.example`
- Production template: `backend/.env.production.example`
- Required production hardening:
  - strong `SECRET_KEY`
  - `COOKIE_SECURE=true`
  - restrictive `CORS_ORIGINS`

## Startup Lifecycle

- API boot command: `sh /app/scripts/start-api.sh`
  - runs `alembic upgrade head`
  - starts gunicorn/uvicorn workers
- Worker boot command: `sh /app/scripts/start-worker.sh`
- Beat boot command: `sh /app/scripts/start-beat.sh`

## Backup and Restore

- Create backup:
  - `sh scripts/backup_postgres.sh backups/srip_YYYYMMDD_HHMM.sql.gz`
- Restore backup:
  - `sh scripts/restore_postgres.sh backups/srip_YYYYMMDD_HHMM.sql.gz`

## Deployment

- Manual:
  - `sh scripts/deploy_compose.sh`
- CI deploy:
  - workflow: `.github/workflows/deploy.yml`
  - build/push to GHCR
  - remote compose rollout + DB migrations over SSH

## Health and Monitoring

- Service health: `/api/v1/health`
- Prometheus metrics: `/metrics`
- Correlation tracing:
  - ingress: `X-Correlation-ID`
  - logs: JSON with `correlation_id`
