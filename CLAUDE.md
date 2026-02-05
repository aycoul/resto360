# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BIZ360 (formerly RESTO360) is a multi-tenant SaaS platform for business operations in West Africa (primarily Côte d'Ivoire). Originally designed for restaurants, it now supports multiple business types: restaurants, cafes, bakeries, retail shops, pharmacies, grocery stores, boutiques, and more.

**Core value:** Businesses can take orders, accept payments, and manage operations — even when internet is unreliable (offline-first architecture).

**Tech stack:**
- Backend: Django 5.x + Django REST Framework + Django Channels (WebSocket)
- Frontend: Next.js 16 with TypeScript (PWA)
- Database: PostgreSQL with PostGIS (spatial features)
- Cache/Queue: Redis + Celery
- Mobile: React Native / Expo (driver and customer apps)

## Commands

### Backend (Django API)

```bash
# All commands run from apps/api directory
cd apps/api

# Activate virtual environment
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # Unix

# Run development server
python manage.py runserver

# Run tests
pytest                        # All tests
pytest apps/orders/           # Single app
pytest -k test_create_order   # Single test by name
pytest -m "not slow"          # Skip slow tests
pytest --cov=apps             # With coverage

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Seed test data
python manage.py seed_test_data

# Linting and formatting
ruff check apps/              # Lint
ruff check apps/ --fix        # Lint and autofix
ruff format apps/             # Format

# Type checking
mypy apps/
```

### Frontend (Next.js)

```bash
# All commands run from apps/web directory
cd apps/web

# Development
pnpm dev                      # Start dev server (port 3000)
pnpm build                    # Production build
pnpm lint                     # ESLint

# E2E tests (Playwright)
pnpm test:e2e                 # Run all E2E tests
pnpm test:e2e:ui              # Interactive UI mode
pnpm test:e2e:headed          # Run with browser visible
pnpm test:e2e:debug           # Debug mode
```

## Architecture

### Multi-Tenancy

All tenant-scoped models inherit from `TenantModel` (`apps/core/models.py`) which has a `business` ForeignKey. The `TenantMiddleware` extracts the current business from the authenticated user's JWT token and sets the tenant context.

```
apps/core/models.py     → BaseModel (UUID pk, timestamps) → TenantModel (+ business FK)
apps/core/middleware.py → TenantMiddleware (extracts business from JWT)
apps/core/context.py    → Thread-local storage for current business
apps/core/managers.py   → TenantManager (auto-filters querysets by current business)
```

### Django App Structure

```
apps/api/apps/
├── core/            # Base models, middleware, permissions, pagination
├── authentication/  # User, Business (formerly Restaurant), JWT auth
├── menu/            # Categories, Products (formerly MenuItems)
├── orders/          # Order, OrderItem
├── payments/        # Payment providers (Wave, Orange, MTN, CinetPay, etc.)
├── inventory/       # Stock items, movements
├── delivery/        # Zones, drivers, deliveries
├── analytics/       # Sales aggregation, reports
├── ai/              # AI menu builder (OpenAI)
├── invoicing/       # DGI electronic invoicing (Ivory Coast tax compliance)
├── forecasting/     # Demand forecasting
└── ...
```

### Payment Providers

All payment providers implement `PaymentProviderBase` abstract class in `apps/payments/providers/base.py`:
- Wave Money, Orange Money, MTN MoMo (direct mobile money)
- Flutterwave, Paystack, CinetPay (aggregators)
- Cash (local recording)

### Frontend Structure

```
apps/web/
├── app/[locale]/         # Next.js App Router with i18n
│   ├── pos/              # POS interface
│   ├── kitchen/          # Kitchen display
│   ├── menu/[slug]/      # Public customer menu
│   ├── track/[id]/       # Delivery tracking
│   └── lite/             # Free tier management UI
├── components/           # Reusable React components
├── lib/                  # Utilities, API client, IndexedDB (Dexie.js)
└── messages/             # i18n translations (fr, en)
```

### Offline-First (PWA)

The POS uses IndexedDB (via Dexie.js) for offline operation:
- Menu items cached locally
- Orders queued in IndexedDB when offline
- Background sync when connection restored
- Idempotency keys prevent duplicate transactions

## Key Conventions

### Naming

- **Business vs Restaurant:** The platform was renamed from RESTO360 to BIZ360. Models use `Business` but maintain `restaurant` property aliases for backwards compatibility.
- **Product vs MenuItem:** Similarly, `Product` is the new name with `MenuItem` aliases.
- Currency: XOF (West African CFA franc) — no decimal places.

### Django Settings

```
config/settings/
├── base.py          # Shared settings
├── development.py   # Local development
├── testing.py       # pytest configuration
├── production.py    # Production (Render.com)
└── local_dev.py     # Local overrides (gitignored)
```

Settings module is selected via `DJANGO_SETTINGS_MODULE` env var.

### Testing

- TDD approach: write tests before implementation
- Use `pytest-factoryboy` for test fixtures (`apps/*/tests/factories.py`)
- Shared fixtures in `apps/api/conftest.py`
- Mock external APIs (payment providers) in tests

### API Design

- REST conventions with DRF ViewSets
- JWT authentication (15 min access, 7 day refresh)
- Standard pagination via `apps.core.pagination.StandardPagination`
- French is primary language, English secondary

### Environment Variables

Key variables (see `apps/api/config/settings/base.py`):
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis for cache and Celery
- `SECRET_KEY` - Django secret
- `FRONTEND_URL` - For QR codes and links
- Payment provider keys: `WAVE_API_KEY`, `ORANGE_CLIENT_ID`, `MTN_SUBSCRIPTION_KEY`, `CINETPAY_API_KEY`, etc.
- `OPENAI_API_KEY` - For AI menu builder
