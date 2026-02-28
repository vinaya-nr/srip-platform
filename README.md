# SRIP — Smart Retail Intelligence Platform

> Production-grade retail management system for small shop owners.
> Retail · Medical · Grocery · Stationery

---

## Built With Vibe Coding

This project was built end-to-end using AI-assisted development:

| What | Tool |
|---|---|
| Architecture — Frontend & Backend | Claude (Sonnet 4.6) |
| Backend Implementation | Codex |
| Backend Unit Tests | Copilot · upgraded by Codex |
| Frontend Implementation | Codex |
| Frontend Unit, Component & E2E Tests | Codex — Vitest + Testing Library + Istanbul |

**Test Coverage**

| Layer | Tests | Coverage |
|---|---|---|
| Backend | 306 passed ✅ | 95.10% |
| Frontend | Statements 100% · Lines 100% · Functions 100% · Branches 98.18% ✅ | Production-grade |

---

## What is SRIP?

SRIP is an open-source platform designed for non-technical shop owners to manage their full retail operation — product catalog, batch inventory, daily sales, stock corrections, and business analytics — without needing any technical background.

**Core capabilities:**
- Product catalog with categories, SKU management, and soft delete
- Batch inventory tracking with expiry alerts and low-stock notifications
- Point-of-sale with automatic stock deduction
- Stock movement corrections (in / out / physical count adjustment)
- Dashboard KPIs, sales history with date-range filters, and analytics snapshots
- Background workers for alerts, nightly reports, and scheduled analytics

---

## Tech Stack at a Glance

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS · shadcn/ui |
| State | TanStack Query v5 · Zustand · React Hook Form + Zod |
| Backend | FastAPI · PostgreSQL 16 · SQLAlchemy · Alembic |
| Background Jobs | Celery + Celery Beat · Redis |
| Auth | JWT (access + refresh tokens) · bcrypt · HttpOnly cookies |
| Infrastructure | Docker · Docker Compose · Nginx · GitHub Actions |

---

## Repository Structure

```
srip_platform/
│
├── frontend/                          # Next.js 14 — App Router
│   ├── app/
│   │   ├── (public)/                  # /login, /register
│   │   ├── (auth)/                    # /logout
│   │   └── (protected)/               # All authenticated pages
│   │       ├── dashboard/
│   │       ├── products/
│   │       ├── categories/
│   │       ├── inventory/
│   │       │   └── movements/new/
│   │       ├── sales/
│   │       │   └── [id]/
│   │       ├── analytics/
│   │       ├── notifications/
│   │       └── settings/
│   ├── components/
│   │   ├── shared/                    # Layout, feedback, forms, data-display
│   │   ├── auth/
│   │   ├── products/
│   │   ├── categories/
│   │   ├── inventory/
│   │   ├── sales/
│   │   ├── analytics/
│   │   └── notifications/
│   ├── lib/
│   │   ├── api/                       # Axios instance + domain clients
│   │   └── hooks/                     # TanStack Query hooks per domain
│   ├── store/                         # Zustand slices (session, cart, ui)
│   ├── types/
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md                      # ← Full frontend detail
│
├── backend/                           # FastAPI application
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                      # config, database, security, logging, exceptions
│   │   ├── middleware/                # Correlation ID, request logging
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── products/
│   │   │   ├── inventory/
│   │   │   ├── sales/
│   │   │   ├── analytics/
│   │   │   └── notifications/
│   │   └── workers/
│   │       ├── celery_app.py
│   │       ├── tasks/                 # stock_alerts, reports, analytics
│   │       └── schedules.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── alembic/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md                      # ← Full backend detail
│
├── docs/
│   └── frontend/                      # Architecture docs (FRONTEND_ARCHITECTURE.md etc.)
│
├── nginx/                             # Reverse proxy config + SSL
├── scripts/                           # DevOps and CI utility scripts
├── docker-compose.yml                 # Full local dev stack
├── docker-compose.prod.yml            # Production overrides
└── README.md                          # ← You are here
```

---

## Quick Start

### Clone

```bash
git clone https://github.com/<your-org>/srip_platform.git
cd srip_platform
```

### Configure

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Minimum variables to set:

```env
# backend/.env
DATABASE_URL=postgresql://srip:srip@postgres:5432/srip
SECRET_KEY=change-me-in-production
REDIS_URL=redis://redis:6379/0

# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Run

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| App (via Nginx) | http://localhost |
| API docs (Swagger) | http://localhost:8000/docs |
| Frontend (direct) | http://localhost:3000 |

### Nginx Routing

```
Browser
   |
nginx (:80 / :443)
   |-- /api/v1/*  →  backend:8000   (FastAPI)
   +-- /*         →  frontend:3000  (Next.js)
```

---

## Application Workflow

### 1 · Register & Sign In
Create a shop account at `/register` (Shop Name, Email, Password) then sign in at `/login`.

### 2 · Setup Master Data
Create categories, then create products with SKU, price, assigned category, and low-stock threshold.

### 3 · Manage Products
Add and edit products inline on the Products page. Search by name/SKU, filter by category, and paginate with Prev/Next. Set Active = No to soft-delete a product — it is hidden from active listings and excluded from new sales.

### 4 · Add Opening Inventory
Go to Inventory → Add Batch and enter product, quantity, unit cost, and expiry date. Repeat for all stocked products.

### 5 · Run Daily Sales
Go to Sales → add products to cart → checkout. Stock is automatically deducted and a sale record is created.

### 6 · Stock Corrections
Use Stock Movement with type `in` (increase batch qty), `out` (reduce batch qty), or `adjustment` (correction after physical count).

### 7 · Monitor Business Health
- **Dashboard** — today's sales count, revenue, low-stock count, unread alerts, top charts
- **Notifications** — low-stock and expiry alerts from background workers; mark as read
- **Analytics** — monthly comparison and nightly snapshot data log

### 8 · Ongoing Operations
Toggle products active/inactive as needed, refill inventory when low-stock alerts appear, and review sales history with date-range filters and sale-detail pages.

### 9 · Background Services
Four services must be running in production — all are defined in `docker-compose.yml` and start automatically with `docker compose up`:

| Service | Role |
|---|---|
| **FastAPI API** | HTTP API for all frontend requests |
| **Redis** | Celery message broker + application cache |
| **Celery Worker** | Stock alerts, report generation, analytics snapshots |
| **Celery Beat** | Scheduler — nightly snapshots, expiry checks, monthly summaries |

---

## Production Deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

CI/CD pipeline is defined in `.github/workflows/`:

```
Push to main → Run Tests → Build Docker Image → Push to GHCR → Deploy via SSH
```

---

## Further Reading

Full detail on architecture, API contracts, testing, and scaling is in the individual READMEs:

- **[backend/README.md](./backend/README.md)** — FastAPI layered architecture, full API reference, auth flow, error handling, structured logging, and scaling guide
- **[frontend/README.md](./frontend/README.md)** — Next.js App Router architecture, route reference, component hierarchy, state management, API integration, and UX patterns
