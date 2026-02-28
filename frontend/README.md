# SRIP Frontend — Smart Retail Intelligence Platform

> Next.js 14 (App Router) frontend for small retail business owners.
> Fast workflows · Accessible UI · Type-safe against backend schemas · Zero vendor lock-in

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Monorepo Placement](#monorepo-placement)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Route Reference](#route-reference)
- [Component Hierarchy](#component-hierarchy)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Authentication & Session](#authentication--session)
- [Error Handling & UX Patterns](#error-handling--ux-patterns)
- [User Workflow](#user-workflow)
- [Deployment](#deployment)
- [Phased Implementation Plan](#phased-implementation-plan)

---

## Overview

This is the **Next.js 14 frontend** for the SRIP platform — a production-grade retail management application for non-technical shop owners in retail, medical, grocery, and stationery businesses.

The frontend lives at `srip_platform/frontend/` inside the monorepo alongside the FastAPI backend. All API communication flows through a single Nginx gateway. Background services (Celery workers, Redis) drive notifications, analytics snapshots, and async tasks — the frontend treats these as async signals, not synchronous responses.

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | Next.js 14 — App Router | Server components, nested layouts, streaming SSR |
| Language | TypeScript (strict mode) | End-to-end type safety against backend schemas |
| Styling | Tailwind CSS + shadcn/ui | Fast, consistent, accessible component primitives |
| Server State | TanStack Query v5 | Declarative caching, background refresh, optimistic updates |
| Client State | Zustand | Lightweight slices for cart, session, and UI state |
| Forms | React Hook Form + Zod | Schema-driven validation mirroring backend rules |
| HTTP Client | Axios + interceptors | Token injection, 401 refresh loop, error normalisation |
| Toast | Sonner | Non-blocking, stackable toast notifications |
| Charts | Recharts | Analytics snapshot rendering |
| Icons | Lucide React | Consistent, tree-shakable icon set |

---

## Monorepo Placement

The frontend is a new top-level sibling of `backend/`. No existing files or folders are changed.

```
srip_platform/
├── backend/                        ← FastAPI app (unchanged)
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   └── ...
├── frontend/                       ← Next.js 14 app (this directory)
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── store/
│   ├── types/
│   ├── public/
│   └── ...
├── docs/
│   └── frontend/                   ← Frontend-specific architecture docs
│       ├── FRONTEND_ARCHITECTURE.md
│       ├── COMPONENT_GUIDE.md      (Phase 2)
│       └── API_CONTRACT.md         (Phase 2)
├── nginx/                          ← Updated: proxies /* to frontend:3000
├── docker-compose.yml              ← Updated: includes frontend service
├── docker-compose.prod.yml
└── README.md
```

### Nginx Routing

```
Browser
   |
   v
nginx  (:80 / :443)
   |-- /api/v1/*  -->  proxy_pass  backend:8000   (FastAPI — unchanged)
   +-- /*         -->  proxy_pass  frontend:3000  (Next.js — added)
```

> **Production note:** Update the `CORS_ORIGINS` backend env var to include the production domain before deploying behind nginx.

---

## Quick Start

### Clone the Repository

```bash
git clone https://github.com/<your-org>/srip_platform.git
cd srip_platform/frontend
```

### Environment Setup

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
NEXT_PUBLIC_APP_NAME=SRIP
```

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL — `http://localhost:8000` (dev) or production domain |
| `NEXT_PUBLIC_APP_ENV` | Environment label: `development` or `production` |
| `NEXT_PUBLIC_APP_NAME` | Display name used in page titles and the app header |

### Run the Full Stack (Recommended)

From the monorepo root:

```bash
docker compose up --build
```

Starts all services: `nginx`, `api`, `frontend`, `worker`, `beat`, `postgres`, `redis`.

### Run Frontend Only (Local Dev)

```bash
npm install
npm run dev
```

App available at `http://localhost:3000`.

### Production Build

```bash
npm run build
npm start
```

---

## Project Structure

```
frontend/
├── app/                                    # Next.js App Router
│   ├── (public)/                           # Unauthenticated routes — no AppShell
│   │   ├── layout.tsx                      # PublicLayout: centered card, brand logo
│   │   ├── page.tsx                        # / → redirect to /dashboard or /login
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (auth)/                             # Auth utility — no AppShell
│   │   └── logout/page.tsx                 # POST /logout → clearSession → /login
│   └── (protected)/                        # Auth-gated via middleware
│       ├── layout.tsx                      # AppShell: sidebar + header
│       ├── dashboard/page.tsx
│       ├── products/page.tsx               # Inline CRUD (single page)
│       ├── categories/page.tsx             # Inline CRUD (single page)
│       ├── inventory/
│       │   ├── page.tsx                    # Batch list — inline CRUD
│       │   └── movements/new/page.tsx      # Stock movement form (separate page)
│       ├── sales/
│       │   ├── page.tsx                    # Sales history
│       │   ├── new/page.tsx                # Point of sale
│       │   └── [id]/page.tsx               # Sale receipt / detail
│       ├── analytics/page.tsx
│       ├── notifications/page.tsx
│       └── settings/page.tsx
│
├── components/
│   ├── shared/                             # Reusable cross-domain components
│   │   ├── layout/                         # AppShell, Sidebar, Header, PageHeader, PublicLayout
│   │   ├── feedback/                       # Toast, ErrorBanner, EmptyState, SkeletonTable,
│   │   │                                   # SkeletonCard, SessionExpiredBanner
│   │   ├── data-display/                   # DataTable, StatCard, StatusBadge, ConfirmDialog
│   │   └── forms/                          # FormField, SearchInput, SelectInput, SubmitButton
│   ├── auth/                               # LoginForm, RegisterForm, SessionExpiredBanner
│   ├── products/                           # ProductTable, ProductRow, ProductEditRow,
│   │                                       # ProductFilters, ProductCard (POS only)
│   ├── categories/                         # CategoryTable, CategoryRow, CategoryEditRow
│   ├── inventory/                          # BatchTable, BatchRow, BatchEditRow, MovementForm,
│   │                                       # ExpiryAlertBanner, LowStockBadge
│   ├── sales/                              # SaleCart, CartItem, ProductSearchPanel,
│   │                                       # SaleTable, SaleDetail, SaleReceiptModal
│   ├── analytics/                          # SnapshotTypeFilter, SalesTrendChart,
│   │                                       # MonthlySummaryChart, NightlySnapshotTable,
│   │                                       # AnalyticsEmptyState
│   └── notifications/                      # NotificationBell, NotificationDropdown,
│                                           # NotificationList, NotificationItem
│
├── lib/
│   ├── api/                                # Axios instance + domain API clients
│   │   ├── axios.ts                        # Base instance, interceptors, error normalisation
│   │   ├── auth.ts
│   │   ├── products.ts
│   │   ├── categories.ts
│   │   ├── inventory.ts
│   │   ├── sales.ts
│   │   ├── analytics.ts
│   │   ├── notifications.ts
│   │   └── users.ts
│   └── hooks/                              # TanStack Query hooks per domain
│       ├── useProducts.ts
│       ├── useCategories.ts
│       ├── useInventory.ts
│       ├── useSales.ts
│       ├── useAnalytics.ts
│       └── useNotifications.ts
│
├── store/                                  # Zustand state slices
│   ├── sessionStore.ts
│   ├── cartStore.ts
│   └── uiStore.ts
│
├── types/                                  # TypeScript view-model definitions
├── public/                                 # Static assets
├── Dockerfile
├── .env.local                              # Local secrets — not committed
├── .env.example                            # Committed template with no secrets
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Architecture

### Core Principles

**Server Components First** — Use React Server Components (RSC) for layout shells, navigation, and initial data fetches. Reserve `'use client'` for interactive islands: forms, charts, real-time polling, and the sale cart.

**Layered API Client** — Communication flows strictly top-down:

```
Axios Instance  (base URL, auth headers, interceptors)
   |
   +-- Domain API Clients  (auth.ts | products.ts | sales.ts | ...)
         |
         +-- TanStack Query Hooks  (useProducts | useSale | ...)
               |
               +-- Feature Components  (ProductTable | SaleCart | ...)
```

**Token Lifecycle is Backend-Driven** — Access token TTL is 15 min. The Axios response interceptor catches 401s, triggers a silent refresh via `POST /api/v1/auth/refresh` (HttpOnly cookie auto-sent by the browser), then retries the original request. Concurrent 401s are queued behind a single in-flight refresh promise to prevent token stampede.

**Implicit Multi-Tenancy** — `shop_id` is embedded in the JWT and applied by the backend on every request. The frontend never manually scopes queries by `shop_id`. Shop context is loaded once via `GET /api/v1/users/me` and cached in the app shell.

**Async-Aware UX** — Backend workers process sales, inventory events, and analytics via Celery/Redis asynchronously. A successful `POST` does not mean all downstream side-effects are complete. Notifications are the observable signal of background task completion — not the HTTP response itself.

### Layout Shells

| Shell | Used By | Key Structural Features |
|---|---|---|
| `PublicLayout` | `/login`, `/register` | Centered card, brand logo, no navigation |
| `AppShell` | All protected pages | Collapsible sidebar, top header, notification bell |
| `FullPageLayout` | Dashboard, Analytics | Max-width container, responsive grid, no inner padding |
| `DetailPageLayout` | Sale receipt, product detail | Breadcrumb + back chevron, sticky action header |
| `DataEntryLayout` | All create/edit forms | Two-column layout, sticky Save/Cancel footer |

---

## Route Reference

| Route | Purpose | Key API Calls | Critical States |
|---|---|---|---|
| `/login` | Sign in | `POST /auth/login` | Idle, submitting, 422 field errors, session-expired banner |
| `/register` | Create shop account | `POST /users` | Idle, submitting, 422 field errors |
| `/dashboard` | KPI command centre | `GET /dashboard/summary`, `GET /users/me`, `GET /notifications?unread_only=true` | Skeleton cards, error banner, empty onboarding prompt |
| `/products` | Products — full inline CRUD | `GET /products`, `GET /categories`, `POST /products`, `PATCH /products/{id}` | Skeleton rows, add-row, edit-row active, 409 SKU inline, 422 field inline |
| `/categories` | Categories — full inline CRUD | `GET /categories`, `POST /categories`, `PATCH /categories/{id}` | Skeleton rows, add-row, edit-row, 409 duplicate name inline |
| `/inventory` | Batch list — inline CRUD | `GET /inventory/batches`, `POST /inventory/batches`, `PATCH /inventory/batches/{id}`, `GET /inventory/alerts/expiry?within_days=15` | Expiry banner, add-row, edit-row, save pending, delete confirm |
| `/inventory/movements/new` | Record stock movement | `POST /inventory/movements` | Conditional `adjustmentMode` field, 422 insufficient stock |
| `/sales` | Sales history | `GET /sales` | Skeleton rows, empty state |
| `/sales/new` | Point of sale | `GET /products`, `POST /sales` | Empty cart, stock error badge, receipt modal |
| `/sales/[id]` | Sale receipt / detail | `GET /sales/{sale_id}` | Loading skeleton, 404 state |
| `/analytics` | Business intelligence | `GET /analytics/snapshots?snapshot_type=...` | Worker-empty state, last-updated timestamp, manual refresh |
| `/notifications` | Alert centre | `GET /notifications`, `PATCH /notifications/{id}/read` | All-read empty state |
| `/settings` | Account config | `GET /users/me` | Read-only in Phase 1 |

---

## Component Hierarchy

### Shared Components

**Layout** — `AppShell`, `Sidebar`, `Header`, `PageHeader`, `PublicLayout`

**Feedback** — `Toast` (via Sonner), `ErrorBanner`, `EmptyState`, `SkeletonTable`, `SkeletonCard`, `SessionExpiredBanner`

**Data Display** — `DataTable` (sortable + paginated), `StatCard`, `StatusBadge`, `ConfirmDialog`

**Forms** — `FormField`, `SearchInput` (debounced 300 ms), `SelectInput`, `SubmitButton`

### Domain Components

| Domain | Key Components |
|---|---|
| Auth | `LoginForm`, `RegisterForm`, `SessionExpiredBanner` |
| Products | `ProductTable`, `ProductRow`, `ProductEditRow` (add + edit inline), `ProductFilters`, `ProductCard` (POS only) |
| Categories | `CategoryTable`, `CategoryRow`, `CategoryEditRow` (add + edit inline) |
| Inventory | `BatchTable`, `BatchRow`, `BatchEditRow`, `MovementForm`, `ExpiryAlertBanner`, `LowStockBadge` |
| Sales | `SaleCart` (Zustand-driven), `CartItem` (qty stepper + error badge), `ProductSearchPanel`, `SaleTable`, `SaleDetail`, `SaleReceiptModal` |
| Analytics | `SnapshotTypeFilter`, `SalesTrendChart` (AreaChart), `MonthlySummaryChart` (BarChart), `NightlySnapshotTable`, `AnalyticsEmptyState` |
| Notifications | `NotificationBell` (badge), `NotificationDropdown` (top 5), `NotificationList`, `NotificationItem` (mark-read) |

---

## State Management

### State Taxonomy

| Category | Tool | Scope | Examples |
|---|---|---|---|
| Server state | TanStack Query | Query cache | Products, sales, snapshots, notifications |
| Form state | React Hook Form | Form component | Login, product add/edit, movement forms |
| UI / client state | Zustand | Global stores | Sidebar open, active modal |
| URL / filter state | Next.js `searchParams` | URL | `?search=` `?category_id=` `?is_active=` |
| Session state | Zustand `sessionStore` | Memory only | `accessToken`, user object |
| Cart state | Zustand `cartStore` | Memory only | `items[]`, computed total |

### Zustand Store Slices

**`sessionStore`**
```typescript
accessToken: string | null
user: { id, email, shopId } | null
setSession(token, user): void
clearSession(): void
isAuthenticated: boolean  // computed
```

**`cartStore`**
```typescript
items: CartItem[]   // { productId, name, price, quantity, maxStock }
addItem(product): void
updateQty(id, qty): void
removeItem(id): void
clearCart(): void
total: number       // computed
```

**`uiStore`**
```typescript
sidebarOpen: boolean
activeModal: null | 'confirm-delete' | 'sale-receipt' | 'expiry-detail'
modalPayload: unknown
openModal(type, payload): void
closeModal(): void
```

### TanStack Query Cache Boundaries

| Query Key | Stale Time | Invalidated After |
|---|---|---|
| `['products', filters]` | 2 min | POST / PATCH / DELETE product |
| `['product', id]` | 5 min | PATCH product |
| `['categories']` | 10 min | POST / PATCH / DELETE category |
| `['inventory-batches', productId]` | 1 min | POST batch, POST movement |
| `['expiry-alerts']` | 5 min | Window focus |
| `['sales']` | 2 min | POST /sales |
| `['analytics-snapshots', type]` | 10 min | Manual refresh button click |
| `['notifications', unreadOnly]` | 30 sec | PATCH /read, window focus |
| `['user-me']` | 15 min | Settings save |

### Optimistic vs Pessimistic Updates

| Action | Strategy | Reason |
|---|---|---|
| Mark notification read | Optimistic | Low risk; instantly improves perceived UX |
| Toggle Active/Inactive (inline edit) | Optimistic | Reversible; rollback on error |
| Inline row Save — POST (add) | Pessimistic | Server validates uniqueness (409); row stays in edit mode on failure |
| Inline row Save — PATCH (edit) | Pessimistic | Server validates uniqueness; row locked until confirmed |
| POST/PATCH `/inventory/batches` | Pessimistic | Server validates product ref and quantity > 0 |
| DELETE product / category / batch | Pessimistic + ConfirmDialog | Destructive; must await server confirmation before removing row |
| POST `/sales` | Pessimistic | Server validates stock; cannot pre-confirm |
| POST `/inventory/movements` | Pessimistic | Backend validates stock sufficiency |

---

## API Integration

### Endpoint Overview

**Auth**
```
POST  /api/v1/auth/login
POST  /api/v1/auth/refresh
POST  /api/v1/auth/logout
POST  /api/v1/users                              # register
GET   /api/v1/users/me
```

**Products & Categories**
```
GET   /api/v1/products                           ?search= ?category_id= ?is_active= ?skip= ?limit=
POST  /api/v1/products
PATCH /api/v1/products/{id}
GET   /api/v1/products/{product_id}/stock        → { product_id, shop_id, current_stock }
GET   /api/v1/categories
POST  /api/v1/categories
PATCH /api/v1/categories/{id}
```

**Inventory**
```
GET   /api/v1/inventory/batches                  ?product_id=
POST  /api/v1/inventory/batches
PATCH /api/v1/inventory/batches/{id}
GET   /api/v1/inventory/alerts/expiry            ?within_days=15
POST  /api/v1/inventory/movements
```

**Sales**
```
GET   /api/v1/sales                              ?skip= ?limit=
POST  /api/v1/sales                              body: [{ product_id, quantity }]
GET   /api/v1/sales/{sale_id}                    → { id, shop_id, sale_number, total_amount, created_at, items[] }
```

**Analytics**
```
GET   /api/v1/analytics/snapshots                ?snapshot_type=
```

**Notifications**
```
GET   /api/v1/notifications                      ?unread_only=true
PATCH /api/v1/notifications/{id}/read
```

**Dashboard**
```
GET   /api/v1/dashboard/summary
→ { today_sales_total, today_revenue_total, active_products_count, low_stock_count, unread_notifications_count }
```

### Pagination

All list endpoints support `?skip=&limit=` with a consistent response envelope:

```json
{ "items": [...], "total": 100, "skip": 0, "limit": 20 }
```

`DataTable` uses server-side pagination. Formula: `skip = (page - 1) * limit`. Default limit: 20. Changing filters resets `skip` to 0.

### Analytics Snapshot Payloads

Snapshot payloads are a flexible `dict` — the backend does not enforce strict schema. Always use optional chaining on all payload field access and render a raw JSON fallback for unknown types.

| `snapshot_type` | Key Payload Fields | Rendered As |
|---|---|---|
| `sale_event` | `sale_id`, `sale_number`, `total_amount`, `items[]` | `SalesTrendChart` (AreaChart) |
| `nightly_snapshot` | `date`, `total_sales`, `total_revenue` | `NightlySnapshotTable` |
| `monthly_summary` | `month`, `total_sales`, `total_revenue` | `MonthlySummaryChart` (BarChart) |

> The Analytics page must always show a "Last updated" timestamp (from `created_at` of the most recent snapshot) and a manual Refresh button. Snapshots are worker-generated and not real-time.

### Notification Polling

`GET /notifications?unread_only=true` runs every 30 seconds via `refetchInterval: 30_000`. The unread count drives the `NotificationBell` badge. No WebSocket or SSE in Phase 1.

### Key Frontend ↔ Backend Field Mappings

**Products**

| Frontend | Backend | Notes |
|---|---|---|
| `productId` | `id` | |
| `categoryId` | `category_id` | camelCased on frontend |
| `lowStockThreshold` | `low_stock_threshold` | |
| `isActive` | `is_active` | |
| `categoryName` | (client join) | Not in API response — joined client-side from categories cache |
| `currentStock` | `GET /products/{id}/stock` | Fetched lazily in POS; advisory only in cart |
| `isLowStock` | derived | Computed on frontend after separate inventory batch fetch |

**Sales**

| Frontend | Backend | Notes |
|---|---|---|
| `saleNumber` | `sale_number` | Display ID on receipt |
| `items[].unitPrice` | `unit_price` | |
| `items[].lineTotal` | `line_total` | |
| `totalAmount` | `total_amount` | Computed by backend |
| `cartItem.productName` | (client only) | Stripped before POST — backend uses `product_id` |

**Inventory**

| Frontend | Backend | Notes |
|---|---|---|
| `expiryDate` | `expiry_date` | ISO 8601 |
| `movementType` | `movement_type` | `in` / `out` / `adjustment` |
| `adjustmentMode` | `adjustment_mode` | Only when `movementType === 'adjustment'` |
| `daysUntilExpiry` | derived | Computed from `expiryDate` on frontend |
| `isExpiringSoon` | derived | `daysUntilExpiry <= 15` |

---

## Authentication & Session

### Token Architecture

| Token | Lifetime | Storage | Purpose |
|---|---|---|---|
| Access Token | 15 min | `sessionStore` (memory only — never `localStorage`) | `Authorization: Bearer` header on every API call |
| Refresh Token | 7 days | HttpOnly cookie (`path=/`) | Silent renewal — browser auto-sends on all requests |

### Session Lifecycle

**App Initialisation:**
```
sessionStore has no accessToken?
   → POST /api/v1/auth/refresh
       |-- 200: restore accessToken into sessionStore, continue to app
       └-- 401: redirect /login  (first visit or cookie expired)
```

**Axios Request Interceptor:** Injects `Authorization: Bearer {accessToken}` on every outgoing request.

**Axios Response Interceptor (on 401):**
```
1. Is refresh already in-flight?  → yes: queue this request, await result
2. No: POST /api/v1/auth/refresh
3. Success: update sessionStore.accessToken, flush all queued requests
4. Failure: clearSession() → /login?reason=session-expired
```

The `SessionExpiredBanner` is conditionally shown on the login page when redirected with `?reason=session-expired`.

Cookie behaviour (confirmed with backend): `REFRESH_COOKIE_PATH=/` — the browser auto-sends the cookie on all requests. Login, refresh, and logout all use the same consistent cookie path setting.

---

## Error Handling & UX Patterns

### HTTP Status → UX Response

| HTTP Status | Trigger | UX Response | Component |
|---|---|---|---|
| 401 | Token expired | Silent refresh → retry; on failure → `/login` | Axios interceptor |
| 404 | Resource missing | Full-page `NotFoundState` with back link | `NotFoundState` |
| 409 | Duplicate resource | Inline field error (e.g. SKU already in use) | RHF `setError()` |
| 422 (form) | Validation failure | Map `error.details` → RHF per-field errors | `FormField` |
| 422 (stock) | Insufficient stock at checkout | Inline `CartItem` error badge; cart stays editable | `CartItem` |
| 500 | Server error | Error toast + `correlationId` displayed for support | `Toast` + `ErrorBanner` |
| Network | Timeout / offline | Toast with Retry CTA | `Toast` |

### Loading Patterns

| Context | Pattern | Component |
|---|---|---|
| Page initial load | Full-section skeleton | `SkeletonTable` or `SkeletonCard` grid |
| Table / list fetch | Skeleton rows (same height as real rows) | `SkeletonTable` |
| Inline row Save | Inputs in that row disabled + Save button spinner; rest of table remains fully interactive | `ProductEditRow` / `BatchEditRow` |
| Delete confirmation | `ConfirmDialog` modal; Confirm button spinner; rest of page not blocked | `ConfirmDialog` |
| Sale confirmation | Full overlay modal + spinner; non-dismissible until confirmed | `SaleReceiptModal` |
| Inline toggle / mark read | Spinner on that element only | Element-local spinner |
| Background refetch | Subtle spinner in page header only — never blocks UI | Header indicator |

### Toast / Banner / Modal Usage

| Channel | Use Case | Auto-dismiss |
|---|---|---|
| Toast — success | Record saved, sale confirmed, movement recorded | 4 sec |
| Toast — error | Non-critical failures, network errors | 6 sec + manual X |
| Toast — info | Background task completed | 5 sec |
| Error banner | Page-load failure with Retry button | Manual dismiss |
| Session banner | Redirected from expired session | Until login completes |
| Inline form error | 422 field-level errors from backend | Cleared on re-submit |
| ConfirmDialog | Delete product / category / batch | Requires user action |
| SaleReceiptModal | Successful sale confirmation | Requires user action |

### Accessibility Standards

- All form inputs have an associated `<label>` element
- Error messages connected via `aria-describedby`
- Modal components trap focus; Escape key closes dismissible modals
- `DataTable` rows are keyboard-navigable (Tab, Enter to open detail)
- Status is never conveyed by colour alone — always pair icon + text with colour
- Minimum touch target: 44×44 px on all interactive elements
- Focus ring always visible — never suppressed with `outline: none`

### Mobile Responsiveness

| Breakpoint | Layout |
|---|---|
| < 640 px (mobile) | Sidebar hidden → bottom tab navigation; tables → card-list view; sale cart → bottom drawer |
| 640–1024 px (tablet) | Sidebar icon-only (collapsed); tables render normally; two-column forms stack vertically |
| > 1024 px (desktop) | Full expanded sidebar; standard two-column layouts |

---

## User Workflow

### 1 · Register Shop Account

- Navigate to `/register`, enter Shop Name, Email, Password
- On success: auto-signed in and redirected to `/dashboard`
- Returning users: sign in at `/login`

### 2 · Setup Master Data

- Create categories at `/categories` — click Add → fill inline row → Save
- Create products at `/products` — click Add → fill inline row:

| Field | Constraint |
|---|---|
| Product Name | Required |
| SKU | Required · Must be unique per shop |
| Category | Required · Cannot be None |
| Price | Required |
| Low Stock Threshold | Required · Must be > 0 |

### 3 · Manage Products

**Add** — click "Add Product" → fill the inline row → Save. Success message appears and the new product is visible in the list.

**Edit** — click Edit on a product row → update any allowed field (name, SKU, category, price, threshold, active flag) → Save. The row is locked during saving; inline success or failure feedback is displayed.

**Deactivate / Soft Delete** — in edit mode, set Active = No → Save. The product is hidden from active listings and excluded from new sales. No data is deleted.

**Search / Filter / Paginate** — use the search input to find by name or SKU, the category dropdown to filter by category, and the Prev/Next pagination controls when the list exceeds the page size.

### 4 · Add Opening Inventory

Navigate to `/inventory` → click "Add Batch" → fill the inline row:

- Product, Quantity, Unit Cost, Expiry Date → Save

Repeat for all stocked products. An `ExpiryAlertBanner` appears for any batch expiring within 15 days.

### 5 · Run Daily Sales

Navigate to `/sales/new`:

- Search for products in the left search panel
- Click "Add to Cart" — items appear in the right-hand `SaleCart` (powered by Zustand `cartStore`)
- Adjust quantities with the stepper; remove items with the × button
- Click "Confirm Sale" — backend validates stock and deducts automatically
- On success: `SaleReceiptModal` displays with the sale number
- On 422 stock error: a per-item error badge appears on the `CartItem`; the cart remains editable

> Stock counts shown in the cart are advisory guidance only. The server is the authority at submit time. Handle 422 errors at submit, not at add-to-cart.

### 6 · Handle Stock Corrections

Navigate to `/inventory/movements/new`:

| Movement Type | Effect |
|---|---|
| `in` | Increase existing batch quantity |
| `out` | Reduce existing batch quantity |
| `adjustment` | Correction after physical count — shows an additional `adjustmentMode` field (increase / decrease) |

### 7 · Monitor Business Health

**Dashboard** (`/dashboard`) — KPI cards: today's sales count, revenue, active product count, low-stock count, unread alerts. Quick-action buttons for New Sale and Add Stock.

**Notifications** (`/notifications`) — low-stock and expiry alerts generated by background workers. Mark individual alerts as read (optimistic update). Unread count shown on the `NotificationBell` badge, polled every 30 seconds.

**Analytics** (`/analytics`) — snapshot charts generated by Celery workers. Filter by snapshot type. The page always shows a "Last updated" timestamp and a manual Refresh button — snapshots are worker-generated, not real-time.

### 8 · Ongoing Operations

- Toggle products active/inactive from the Products page as stock changes or products are discontinued
- Refill inventory from the Inventory page when low-stock notifications appear
- Review sales history at `/sales` with date filters and click any row to view the receipt at `/sales/[id]`

### 9 · Background Services (Required in Production)

These four services drive notifications, snapshots, and async analytics tasks. All are defined in `docker-compose.yml`:

| Service | Role |
|---|---|
| **FastAPI API** | All HTTP API calls from this frontend |
| **Redis** | Celery broker + application cache |
| **Celery Worker** | Stock alerts, report generation, analytics snapshots |
| **Celery Beat** | Scheduled periodic tasks — nightly snapshots, monthly summaries, expiry checks |

> A successful API response does **not** mean all background tasks are complete. Notifications are the observable signal of async task completion.

---

## Deployment

### Docker Compose

The frontend service added to `docker-compose.yml`:

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
      - NEXT_PUBLIC_APP_ENV=development
    depends_on:
      - backend
```

### Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### CI/CD

Defined in `.github/workflows/`:

```
Push to main → Run Tests → Build Docker Image → Push to GHCR → Deploy via SSH
```

---

## Phased Implementation Plan

### Phase 1 — MVP: Core Retail Operations

| Sprint | Deliverable | Routes | Key Technical Work |
|---|---|---|---|
| S1 | Repo scaffold + Auth + AppShell | `/login` `/register` `/dashboard` (stub) | Create `frontend/` in monorepo, Dockerfile, `.env.example`, Axios instance + interceptors, `sessionStore`, on-init refresh, AppShell, nginx update, docker-compose update |
| S2 | Products — inline CRUD | `/products` | `ProductTable`, `ProductEditRow` (add + edit), `ProductFilters`, RHF+Zod, 409 SKU inline error, `ConfirmDialog` delete, `ProductCard` for POS reuse |
| S3 | Categories — inline CRUD | `/categories` | `CategoryTable`, `CategoryEditRow` (add + edit), 409 duplicate name inline error |
| S4 | Inventory — inline CRUD + Movement | `/inventory`, `/inventory/movements/new` | `BatchTable`, `BatchEditRow`, `ExpiryAlertBanner`, `MovementForm` with conditional `adjustmentMode` field |
| S5 | Sales — POS | `/sales/new` `/sales` `/sales/[id]` | `cartStore` (Zustand), `ProductSearchPanel`, `SaleCart`, `CartItem`, `SaleReceiptModal`, 422 stock error UX |
| S6 | Notifications + Dashboard | `/notifications` `/dashboard` (complete) | Notification polling, `NotificationBell`, `StatCard` grid, alert panel, quick-action buttons |

### Phase 2 — Hardening & Intelligence

| Sprint | Deliverable | Key Work |
|---|---|---|
| S7 | Analytics Dashboard | Chart rendering by `snapshot_type`, payload type guards, `AnalyticsEmptyState` with worker schedule note, manual refresh |
| S8 | Mobile Optimisation | Bottom tab navigation, card-list tables on mobile, `SaleCart` as bottom drawer, touch-target audit |
| S9 | Advanced Error Handling | Correlation ID in toasts, `NotFoundState`, `ErrorBoundary` wrappers, retry patterns |
| S10 | Accessibility Audit | Focus management, ARIA labels, keyboard nav, colour-contrast audit |
| S11 | Settings Page | Shop profile update (requires `PATCH /api/v1/users/me` — Phase 2 backend API) |
| S12 | Observability | Sentry integration, Web Vitals reporting, structured frontend error logging |

### Planned Phase 2 APIs

| Endpoint | Purpose | Priority |
|---|---|---|
| `GET /api/v1/notifications/stream` (SSE) | Real-time push to replace 30 s polling | Medium |
| `PATCH /api/v1/users/me` | Update shop name from Settings page | Medium |
| `POST /api/v1/auth/change-password` | Password management in Settings | Low |
