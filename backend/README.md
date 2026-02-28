# SRIP Backend — Smart Retail Intelligence Platform

> Production-grade FastAPI backend for small retail business owners.
> Simple workflows · Beginner-friendly codebase · AI/ML ready · Zero vendor lock-in

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [User Workflow](#user-workflow)
- [API Reference](#api-reference)
- [Authentication](#authentication)
- [Background Services](#background-services)
- [Error Handling](#error-handling)
- [Logging & Tracing](#logging--tracing)
- [Deployment](#deployment)
- [Scaling](#scaling)
- [Testing](#testing)
- [Recent Updates](#recent-updates)

---

## Overview

SRIP (Smart Retail Intelligence Platform) is an open-source retail management platform built for non-technical shop owners — retail, medical, grocery, stationery. The backend is intentionally low-complexity: no over-engineering, ship fast, scale smart.

A **Next.js frontend** communicates exclusively with this **FastAPI backend** through a single HTTPS gateway. All business logic lives here. Async background jobs powered by **Celery + Redis** handle alerts, snapshots, and scheduled analytics — keeping the main API fast and responsive.

**Current status:** 315 tests passing · 95.25% total coverage

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI (Python) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy + Alembic |
| Auth | JWT (access + refresh tokens) + bcrypt |
| Background Jobs | Celery + Celery Beat |
| Message Broker / Cache | Redis 7 |
| Reverse Proxy | Nginx |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions → GHCR |
| File Storage | MinIO (S3-compatible, optional) |

---

## Quick Start

### Clone the Repository

```bash
git clone https://github.com/<your-org>/srip_platform.git
cd srip_platform/backend
```

### Environment Setup

Create a `.env` file in `backend/`:

```env
DATABASE_URL=postgresql://srip:srip@postgres:5432/srip
SECRET_KEY=your-secret-key-change-in-production
REDIS_URL=redis://redis:6379/0
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
LOG_LEVEL=INFO
```

### Run with Docker Compose (Recommended)

From the project root:

```bash
docker compose up --build
```

This starts all required services: `nginx`, `api`, `frontend`, `worker`, `beat`, `postgres`, `redis`.

### Run API Locally (Without Docker)

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Apply Database Migrations

```bash
alembic upgrade head
```

### Interactive API Docs

| Interface | URL |
|---|---|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

---

## Architecture

### Layered Request Flow

The backend enforces a **single, unbreakable data flow**. No layer may skip another.

```
Request → Router → Service → Repository → Model (DB) → Response
```

| # | Layer | File | Responsibility | Cannot Touch |
|---|---|---|---|---|
| 1 | **Router** | `modules/*/router.py` | Receive HTTP request · Validate input with Pydantic · Call service · Return response | Database, raw SQL, business logic |
| 2 | **Service** | `modules/*/service.py` | All business logic · Orchestrates repositories · Raises typed exceptions | HTTP details, request/response objects |
| 3 | **Repository** | `modules/*/repository.py` | SQLAlchemy DB access only · Pure CRUD · Always filters by `shop_id` | Business rules, HTTP, email, jobs |
| 4 | **Model** | `modules/*/models.py` | SQLAlchemy ORM table definitions only · Zero logic | Everything — pure class definitions |

### Core Infrastructure Layer

`app/core/` is a shared toolbox — not part of the request flow, but imported by all layers:

| File | Imported By | Purpose |
|---|---|---|
| `core/config.py` | Everything | Pydantic `BaseSettings` — single source of truth for all env vars |
| `core/database.py` | Repositories, `dependencies.py` | SQLAlchemy engine, `SessionLocal`, `Base`, `get_db()` |
| `core/dependencies.py` | All Routers | `get_current_user()` and `get_current_shop()` via FastAPI `Depends()` |
| `core/security.py` | Auth service, `dependencies.py` | JWT create/verify, bcrypt hash/verify, Redis-backed token blacklisting |
| `core/logging.py` | `main.py` (once at startup) | JSON log format, log level, `correlation_id` contextvar |
| `core/exceptions.py` | All Services, `main.py` | Custom exception hierarchy + global FastAPI exception handlers |

### Feature Modules

| Feature | Module | Background Job? | DB Tables |
|---|---|---|---|
| Product Management | `app/modules/products/` | No | `products`, `categories` |
| Stock / Inventory | `app/modules/inventory/` | Yes — expiry alerts | `stock_movements`, `batches` |
| Sales | `app/modules/sales/` + `reports/` | Yes — monthly gen | `sales`, `sale_items` |
| Analytics | `app/modules/analytics/` | Yes — nightly batch | `analytics_snapshots` |
| Auth / Users | `app/modules/auth/` + `users/` | No | `users`, `shops` |
| Notifications | `app/modules/notifications/` | Yes — event driven | `notifications` |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                           # FastAPI app factory — middleware, routers, startup
│   ├── core/
│   │   ├── config.py                     # All env vars via Pydantic BaseSettings
│   │   ├── database.py                   # SQLAlchemy engine, SessionLocal, Base, get_db()
│   │   ├── dependencies.py               # FastAPI Depends(): get_current_user(), get_current_shop()
│   │   ├── security.py                   # JWT, bcrypt, token blacklist (Redis)
│   │   ├── logging.py                    # JSON log config, correlation_id contextvar
│   │   └── exceptions.py                 # Exception hierarchy + global handlers
│   ├── middleware/
│   │   ├── correlation.py                # X-Correlation-ID header: extract → store → respond
│   │   └── logging.py                    # HTTP request/response logging middleware
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py                 # POST /login, /refresh, /logout
│   │   │   ├── service.py
│   │   │   └── schemas.py                # LoginSchema, TokenResponseSchema, TokenPayload
│   │   ├── products/                     # 5-file pattern ↓
│   │   │   ├── router.py                 # CRUD endpoints
│   │   │   ├── service.py                # Business logic
│   │   │   ├── repository.py             # DB queries (always filters by shop_id)
│   │   │   ├── schemas.py                # Create / Update / Response / Filter schemas
│   │   │   └── models.py                 # SQLAlchemy ORM model
│   │   ├── inventory/                    # (same 5-file pattern)
│   │   ├── sales/                        # (same 5-file pattern + date-range filter support)
│   │   ├── analytics/                    # (same 5-file pattern)
│   │   └── notifications/                # (same 5-file pattern)
│   └── workers/
│       ├── celery_app.py                 # Celery app + Redis broker (reads from core/config.py)
│       ├── tasks/
│       │   ├── stock_alerts.py           # check_low_stock, check_expiry_dates
│       │   ├── reports.py                # generate_daily_report, monthly_summary
│       │   └── analytics.py              # compute_slow_movers, nightly_snapshot
│       └── schedules.py                  # Celery Beat schedule definitions
├── tests/
│   ├── unit/
│   │   └── test_sales_service.py         # Sales date-filter unit tests
│   └── integration/
│       └── test_new_endpoints_router.py  # Router-level integration tests
├── alembic/                              # Database migrations
├── requirements.txt                      # Pinned production dependencies
├── requirements-dev.txt                  # pytest, black, ruff, mypy
└── Dockerfile                            # Multi-stage: deps → app → production
```

---

## User Workflow

### 1 · Register Shop Account

- `POST /api/v1/auth/register` — provide Shop Name, Email, Password
- `POST /api/v1/auth/login` — returns `access_token` (JWT) and sets `refresh_token` HttpOnly cookie

### 2 · Setup Master Data

- Create categories: `POST /api/v1/categories`
- Create products: `POST /api/v1/products` — assign category, SKU, price, low-stock threshold

### 3 · Manage Products

**Add** — `POST /api/v1/products`

| Field | Constraint |
|---|---|
| `name` | Required |
| `sku` | Required · Must be unique per shop |
| `category_id` | Required · Cannot be null |
| `price` | Required |
| `low_stock_threshold` | Required · Must be > 0 |

**Edit** — `PATCH /api/v1/products/{id}`
Update any combination of: name, SKU, category, price, threshold, `is_active`.

**Deactivate / Soft Delete**
Set `is_active: false` via edit. Product is hidden from active listings and excluded from new sales. No data is deleted.

**List / Search / Filter** — `GET /api/v1/products`

| Query Param | Description |
|---|---|
| `search` | Filter by name or SKU |
| `category_id` | Filter by category |
| `page` / `page_size` | Pagination (Prev / Next) |

### 4 · Add Opening Inventory

`POST /api/v1/inventory/batches` — provide product, quantity, unit cost, expiry date. Repeat for all stocked products.

### 5 · Run Daily Sales

`POST /api/v1/sales` — submit cart items and checkout. Stock is automatically deducted from batches (FIFO by expiry date) and a sale record is created.

### 6 · Handle Stock Corrections

`POST /api/v1/inventory/movements` with movement type:

| Type | Effect |
|---|---|
| `in` | Increase existing batch quantity |
| `out` | Reduce existing batch quantity |
| `adjustment` | Correction after physical stock count |

### 7 · Monitor Business Health

| Endpoint | What it shows |
|---|---|
| `GET /api/v1/dashboard` | Today's sales count, revenue, low-stock count, unread alerts, top charts |
| `GET /api/v1/notifications` | Low-stock and expiry alerts |
| `PATCH /api/v1/notifications/{id}/read` | Mark alert as read |
| `GET /api/v1/analytics` | Monthly comparison, data log view |

### 8 · Ongoing Operations

- Toggle `is_active` on products as inventory changes or products are discontinued
- Refill inventory when low-stock notifications appear
- Review sales history using date-range filters (see Sales API below)

---

## API Reference

### Auth

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
```

### Products

```
GET    /api/v1/products                    # List — supports search, category filter, pagination
POST   /api/v1/products                    # Create product
GET    /api/v1/products/{id}               # Get product detail
PATCH  /api/v1/products/{id}               # Update product
```

### Inventory

```
GET    /api/v1/inventory/batches            # List batches
POST   /api/v1/inventory/batches            # Add batch
POST   /api/v1/inventory/movements          # Record stock movement (in / out / adjustment)
```

### Sales

```
GET    /api/v1/sales                        # Sales history — supports date-range filter
POST   /api/v1/sales                        # Create sale (checkout)
GET    /api/v1/sales/{id}                   # Sale detail
```

**Date-range filtering on `GET /api/v1/sales`:**

| Query Param | Type | Required | Description |
|---|---|---|---|
| `from_date` | `YYYY-MM-DD` | No | Start of range · inclusive · applied at `00:00:00` |
| `to_date` | `YYYY-MM-DD` | No | End of range · inclusive · applied at `23:59:59` |
| `skip` | integer | No | Pagination offset |
| `limit` | integer | No | Page size |

Validation rule: `from_date` must be ≤ `to_date`. An invalid range returns HTTP 422 with code `VALIDATION_FAILED`. Date boundaries are applied as full-day inclusive to ensure expected behavior when filtering by calendar date.

### Analytics

```
GET    /api/v1/analytics/snapshots
GET    /api/v1/analytics/top-products
GET    /api/v1/analytics/revenue-series
GET    /api/v1/analytics/monthly-comparison
GET    /api/v1/analytics/revenue-profit-summary
```

### Notifications

```
GET    /api/v1/notifications                # List alerts
PATCH  /api/v1/notifications/{id}/read      # Mark as read
```

### Dashboard

```
GET    /api/v1/dashboard
```

---

## Authentication

SRIP uses **JWT-based auth** with the industry-standard secure token pattern:

| Token | Lifetime | Storage | Purpose |
|---|---|---|---|
| Access Token | 15 minutes | React memory only (never `localStorage`) | API authorization — sent as `Authorization: Bearer <token>` |
| Refresh Token | 7 days | HttpOnly cookie (server-set, not readable by JS) | Silently obtain new access token |

**JWT Payload:**

```json
{
  "sub":     "<user_id UUID>",
  "shop_id": "<UUID — enforces tenant isolation on every DB query>",
  "jti":     "<unique token ID — blacklisted in Redis on logout>",
  "exp":     "<unix timestamp>",
  "iat":     "<unix timestamp>"
}
```

SRIP uses a **single-user-per-shop model** — no roles, no permission matrix. Any authenticated user has full access to their own shop's data and nothing else. The `shop_id` in the JWT is injected into every repository query, making cross-shop data leaks structurally impossible.

---

## Background Services

All four services are required in production. All are defined in `docker-compose.yml`:

| Service | Role |
|---|---|
| **FastAPI API** | Main HTTP API — all user-facing requests |
| **Redis** | Celery message broker + application cache layer |
| **Celery Worker** | Executes async tasks: stock alerts, report generation, analytics |
| **Celery Beat** | Periodic task scheduler — **run exactly one instance** |

### Scheduled Tasks

| Task | File | Schedule | Description |
|---|---|---|---|
| `check_low_stock` | `tasks/stock_alerts.py` | Every 30 min | Detect products below threshold, create notifications |
| `check_expiry_dates` | `tasks/stock_alerts.py` | Daily | Flag batches expiring within 7 days |
| `generate_daily_report` | `tasks/reports.py` | Daily at midnight | Summarize day's sales and stock |
| `monthly_summary` | `tasks/reports.py` | 1st of each month | Generate monthly business insights |
| `nightly_snapshot` | `tasks/analytics.py` | Nightly | Pre-aggregate analytics into `analytics_snapshots` |

> **Warning:** Run exactly **one** Celery Beat instance. Multiple beat instances will cause duplicate scheduled task executions.

---

## Error Handling

Every error — validation failure, 404, or unexpected crash — returns the same JSON envelope:

```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "No product with ID abc123 found in your shop.",
    "details": null,
    "correlation_id": "a3f2b891-...",
    "timestamp": "2025-01-15T10:30:45Z"
  }
}
```

For validation errors, `details` is populated with field-level information:

```json
"details": [
  { "field": "price",     "msg": "must be greater than 0" },
  { "field": "from_date", "msg": "from_date must be less than or equal to to_date" }
]
```

**Exception hierarchy:**

```
SRIPBaseException
├── NotFoundException            → HTTP 404   (product / sale not found)
├── DuplicateException           → HTTP 409   (SKU already exists in shop)
├── AuthorizationException       → HTTP 403   (cross-shop access attempt)
├── ValidationException          → HTTP 422   (business rule violation, e.g. invalid date range)
└── ExternalServiceException     → HTTP 503   (email / SMS service down)
Unhandled Python Exception       → HTTP 500   (full traceback logged server-side, safe envelope to client)
```

Raw Python tracebacks never reach the client. The global exception handler is the single last line of defense.

---

## Logging & Tracing

All logs are structured JSON. Every log line carries a `correlation_id` that traces a request end-to-end across Nginx → Middleware → Router → Service → Repository → Celery worker.

```json
{
  "timestamp":      "2025-01-15T10:30:45.123Z",
  "level":          "INFO",
  "correlation_id": "a3f2b891-...",
  "service":        "srip-api",
  "module":         "app.modules.inventory.service",
  "event":          "low_stock_detected",
  "user_id":        "uuid-...",
  "shop_id":        "uuid-...",
  "duration_ms":    142,
  "extra":          { "product_id": "uuid", "stock": 3, "threshold": 5 }
}
```

`X-Correlation-ID` is generated by Nginx if absent, propagated through every layer, and returned in the HTTP response header for support ticket tracing.

| Level | When to use |
|---|---|
| `DEBUG` | Dev/testing only — SQL queries, payload inspection |
| `INFO` | Normal operation — request received, product created, job started |
| `WARNING` | Recoverable issues — low stock detected, slow DB query (> 500 ms) |
| `ERROR` | Expected failures — validation failed, unauthorized access attempt |
| `CRITICAL` | System in danger — DB connection lost, disk full |

---

## Deployment

### Docker Compose Services

| Service | Image | Exposure | Notes |
|---|---|---|---|
| `nginx` | `nginx:alpine` | 80, 443 (public) | Only public-facing service |
| `api` | `./backend` | 8000 (internal) | FastAPI + Gunicorn, 2–4 workers |
| `frontend` | `./frontend` | 3000 (internal) | Next.js SSR |
| `worker` | `./backend` (same image) | None | Celery worker, scale as needed |
| `beat` | `./backend` (same image) | None | Celery Beat — **1 instance only** |
| `postgres` | `postgres:16-alpine` | 5432 (internal) | Persistent volume |
| `redis` | `redis:7-alpine` | 6379 (internal) | Broker + cache |

### Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### CI/CD Pipeline

```
Push to main → Run Tests (pytest) → Build Docker Image → Push to GHCR → Deploy via SSH
```

Pipeline defined in `.github/workflows/`.

### Zero Vendor Lock-in

Every component is open-source and self-hostable. No proprietary cloud service is required at any stage.

| Component | Open Source Solution |
|---|---|
| Container runtime | Docker + Docker Compose (or k3s / k8s) |
| Reverse proxy | Nginx |
| Database | PostgreSQL 16 (self-hosted container) |
| Cache / broker | Redis 7 |
| File storage | MinIO (S3-compatible) |
| Logs / monitoring | Structured JSON → stdout · Grafana + Loki (optional) |
| CI/CD | GitHub Actions → GHCR (free) |

---

## Scaling

SRIP runs comfortably on a single Docker Compose host for hundreds of concurrent users. Scale individual components only when observability data confirms the need — not before.

| Component | Scale When | How |
|---|---|---|
| API | CPU > 70% or p95 latency > 300 ms | `docker compose up --scale api=3` |
| Celery Workers | Queue depth > 500 tasks or job lag > 60 s | `docker compose up --scale worker=4` |
| PostgreSQL | Connection wait time rising | Add PgBouncer in front of Postgres |
| Redis | Cache hit rate < 70% or memory > 80% | Increase `maxmemory`, set `allkeys-lru` eviction |
| Read load | DB reads > 80% of total queries | Add PostgreSQL read replica |

Kubernetes (k3s or standard k8s) is supported — the same Docker images deploy directly with no application code changes required.

---

## Testing

```bash
cd backend
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/
```

**Current test status:**

| Metric | Value |
|---|---|
| Total tests | 315 passed |
| Total coverage | 95.25% |

**Key test files:**

| File | Scope | Covers |
|---|---|---|
| `tests/unit/test_sales_service.py` | Unit | `from_date`/`to_date` passed through service → repository · Invalid date range rejection |
| `tests/integration/test_new_endpoints_router.py` | Integration | Sales list with date filters · Invalid date-range error path · Analytics endpoint routing and response contracts (snapshots, top-products, revenue-series, monthly-comparison, revenue-profit-summary) |

---

## Recent Updates

### Sales History Date-Range Filtering

`GET /api/v1/sales` now supports optional `from_date` and `to_date` query parameters alongside existing `skip` and `limit` pagination params.

The implementation spans three layers with no database schema or migration change required:

`router.py` — accepts `from_date` and `to_date` as optional query parameters and passes them to the service layer.

`service.py` — validates that `from_date ≤ to_date`. An invalid range raises a `ValidationException` returned as HTTP 422 with code `VALIDATION_FAILED`.

`repository.py` — applies the date filter with full-day inclusive boundaries (`from_date` at `00:00:00`, `to_date` at `23:59:59`) ensuring expected behavior for calendar-day filtering.

This change is API / service / repository logic and tests only — no DB migration required.
