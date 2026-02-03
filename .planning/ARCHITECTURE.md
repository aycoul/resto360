# RESTO360 - System Architecture Document

**Version:** 1.0
**Date:** 2026-02-03
**Status:** Foundation Blueprint

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Project Structure](#2-project-structure)
3. [Database Schema Design](#3-database-schema-design)
4. [API Design Principles](#4-api-design-principles)
5. [Development Workflow](#5-development-workflow)
6. [Security Architecture](#6-security-architecture)
7. [Testing Strategy](#7-testing-strategy)
8. [Deployment Architecture](#8-deployment-architecture)
9. [12-Week Build Phases](#9-12-week-build-phases)

---

## 1. System Architecture

### 1.1 High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   CLIENTS                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│   │   POS App    │    │ Customer App │    │  Driver App  │    │  Admin Web   │ │
│   │  (Next.js)   │    │(React Native)│    │(React Native)│    │  (Next.js)   │ │
│   │    PWA       │    │    Expo      │    │    Expo      │    │              │ │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
│          │                   │                   │                   │          │
│          │              ┌────┴────┐              │                   │          │
│          │              │         │              │                   │          │
│   ┌──────┴──────────────┴─────────┴──────────────┴───────────────────┴───────┐ │
│   │                        CLOUDFLARE CDN + WAF                              │ │
│   └─────────────────────────────────┬────────────────────────────────────────┘ │
└─────────────────────────────────────┼────────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼────────────────────────────────────────────┐
│                              RENDER PLATFORM                                      │
├─────────────────────────────────────┼────────────────────────────────────────────┤
│                                     ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         NGINX (API Gateway)                              │   │
│   │                    Rate Limiting │ SSL Termination                       │   │
│   └─────────────────────────────────┬───────────────────────────────────────┘   │
│                                     │                                            │
│   ┌─────────────────────────────────┼───────────────────────────────────────┐   │
│   │                                 ▼                                        │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │                    DJANGO REST API                               │   │   │
│   │   │                   (Gunicorn + Uvicorn)                          │   │   │
│   │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │   │
│   │   │  │  Auth   │ │   POS   │ │ Orders  │ │Payments │ │Delivery │   │   │   │
│   │   │  │  App    │ │   App   │ │   App   │ │   App   │ │   App   │   │   │   │
│   │   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │   │
│   │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │   │
│   │   │  │WhatsApp │ │Suppliers│ │ Finance │ │Analytics│ │  Core   │   │   │   │
│   │   │  │   App   │ │   App   │ │   App   │ │   App   │ │  App    │   │   │   │
│   │   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │   │
│   │   └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │                    CELERY WORKERS                                │   │   │
│   │   │         Background Tasks │ Webhooks │ Notifications              │   │   │
│   │   └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                            │
│   ┌─────────────────────────────────┼───────────────────────────────────────┐   │
│   │                          DATA LAYER                                      │   │
│   │                                 │                                        │   │
│   │   ┌─────────────┐    ┌─────────┴─────────┐    ┌─────────────────────┐   │   │
│   │   │  PostgreSQL │    │       Redis       │    │     Cloudinary      │   │   │
│   │   │   (Primary) │    │   Cache + Queue   │    │   (Image Storage)   │   │   │
│   │   │             │    │                   │    │                     │   │   │
│   │   └─────────────┘    └───────────────────┘    └─────────────────────┘   │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼────────────────────────────────────────────┐
│                          EXTERNAL INTEGRATIONS                                    │
├─────────────────────────────────────┼────────────────────────────────────────────┤
│                                     ▼                                            │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐│
│   │    Wave     │  │   Orange    │  │  MTN MoMo   │  │      WhatsApp API       ││
│   │    API      │  │  Money API  │  │    API      │  │  (Meta / Twilio TBD)    ││
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────┘│
│                                                                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                             │
│   │   Sentry    │  │ Better Stack│  │  SendGrid   │                             │
│   │ (Errors)    │  │  (Logging)  │  │  (Email)    │                             │
│   └─────────────┘  └─────────────┘  └─────────────┘                             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow - Order Lifecycle

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              ORDER LIFECYCLE                                      │
└──────────────────────────────────────────────────────────────────────────────────┘

    POS/WhatsApp/App                API                    Kitchen              Delivery
         │                           │                        │                    │
         │  1. Create Order          │                        │                    │
         ├──────────────────────────►│                        │                    │
         │                           │                        │                    │
         │                           │  2. Validate & Save    │                    │
         │                           ├───────┐                │                    │
         │                           │       │                │                    │
         │                           │◄──────┘                │                    │
         │                           │                        │                    │
         │                           │  3. Push to Kitchen    │                    │
         │                           ├───────────────────────►│                    │
         │                           │                        │                    │
         │  4. Payment Request       │                        │                    │
         ├──────────────────────────►│                        │                    │
         │                           │                        │                    │
         │     ┌─────────────────────┤                        │                    │
         │     │ 5. Call Payment API │                        │                    │
         │     │    (Wave/Orange/MTN)│                        │                    │
         │     └─────────────────────┤                        │                    │
         │                           │                        │                    │
         │  6. Payment Confirmed     │                        │                    │
         │◄──────────────────────────┤                        │                    │
         │                           │                        │                    │
         │                           │  7. Kitchen Complete   │                    │
         │                           │◄───────────────────────┤                    │
         │                           │                        │                    │
         │                           │  8. Assign Driver      │                    │
         │                           ├────────────────────────┼───────────────────►│
         │                           │                        │                    │
         │                           │  9. Real-time Updates  │                    │
         │◄──────────────────────────┼────────────────────────┼───────────────────►│
         │         (WebSocket)       │                        │                    │
         │                           │                        │                    │
         │                           │  10. Delivered         │                    │
         │◄──────────────────────────┼────────────────────────┼───────────────────►│
         │                           │                        │                    │
```

### 1.3 Offline-First POS Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         POS TABLET (OFFLINE-FIRST)                                │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         Next.js PWA (Service Worker)                     │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│   │  │    Menu     │  │   Orders    │  │   Sync      │  │   Payment   │    │   │
│   │  │   Cache     │  │   Queue     │  │   Manager   │  │   Handler   │    │   │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │   │
│   │         │                │                │                │            │   │
│   │         └────────────────┼────────────────┼────────────────┘            │   │
│   │                          │                │                              │   │
│   │                          ▼                ▼                              │   │
│   │                   ┌─────────────────────────────┐                       │   │
│   │                   │        IndexedDB            │                       │   │
│   │                   │   (Dexie.js Wrapper)        │                       │   │
│   │                   │                             │                       │   │
│   │                   │  • menu_items (cached)      │                       │   │
│   │                   │  • pending_orders (queue)   │                       │   │
│   │                   │  • pending_payments         │                       │   │
│   │                   │  • sync_log                 │                       │   │
│   │                   └─────────────────────────────┘                       │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                            │
│                    ┌────────────────┼────────────────┐                          │
│                    │    ONLINE      │     OFFLINE    │                          │
│                    │                │                │                          │
│                    ▼                ▼                ▼                          │
│            ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│            │ Sync to API │  │ Queue Local │  │ Show Cached │                   │
│            │ Immediately │  │   Orders    │  │    Menu     │                   │
│            └─────────────┘  └─────────────┘  └─────────────┘                   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

CONFLICT RESOLUTION STRATEGY (Recommended):

┌──────────────────────────────────────────────────────────────────────────────────┐
│ APPROACH: Operation-Based Sync with Server Authority                             │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│ 1. ORDERS: Append-Only (No Conflicts)                                           │
│    • Orders created offline get local UUID + "pending" status                   │
│    • On sync: server assigns canonical order_number, local UUID preserved       │
│    • Order modifications queue as separate "order_update" operations            │
│                                                                                  │
│ 2. MENU/INVENTORY: Server Wins                                                  │
│    • Menu is read-only on POS                                                   │
│    • Periodic cache refresh (every 15 min online, full sync on reconnect)       │
│    • Stock counts: server is authoritative, POS shows "may be stale" warning    │
│                                                                                  │
│ 3. PAYMENTS: Idempotent Operations                                              │
│    • Each payment attempt has unique idempotency_key                            │
│    • Retry safe: server deduplicates by idempotency_key                        │
│    • Cash payments: immediate local confirmation, sync for records              │
│                                                                                  │
│ 4. SYNC QUEUE STRUCTURE:                                                        │
│    {                                                                             │
│      "id": "uuid-v4",                                                           │
│      "operation": "CREATE_ORDER | UPDATE_ORDER | PAYMENT",                      │
│      "payload": { ... },                                                        │
│      "created_at": "ISO-8601",                                                  │
│      "retry_count": 0,                                                          │
│      "idempotency_key": "uuid-v4"                                               │
│    }                                                                             │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Multi-Tenancy Model

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-TENANCY: Shared Database, Row-Level Isolation           │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  APPROACH: Single database with restaurant_id foreign key on all tenant tables  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                          PostgreSQL Database                               │ │
│  │                                                                            │ │
│  │   SHARED TABLES              TENANT TABLES (have restaurant_id FK)        │ │
│  │   ┌──────────────┐          ┌───────────────────────────────────────────┐ │ │
│  │   │ restaurants  │          │  users (staff per restaurant)             │ │ │
│  │   │ plans        │          │  menu_categories                          │ │ │
│  │   │ features     │          │  menu_items                               │ │ │
│  │   │ payment_     │          │  orders                                   │ │ │
│  │   │  providers   │          │  order_items                              │ │ │
│  │   └──────────────┘          │  payments                                 │ │ │
│  │                             │  customers                                │ │ │
│  │                             │  deliveries                               │ │ │
│  │                             │  inventory                                │ │ │
│  │                             │  suppliers                                │ │ │
│  │                             └───────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  IMPLEMENTATION:                                                                 │
│                                                                                  │
│  1. TenantMiddleware extracts restaurant from JWT/session                       │
│  2. Custom QuerySet manager auto-filters by current tenant                      │
│  3. All API views use tenant-aware querysets                                    │
│  4. PostgreSQL Row-Level Security (RLS) as defense-in-depth                    │
│                                                                                  │
│  # managers.py                                                                   │
│  class TenantManager(models.Manager):                                           │
│      def get_queryset(self):                                                    │
│          restaurant = get_current_restaurant()                                  │
│          return super().get_queryset().filter(restaurant=restaurant)            │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

### 2.1 Monorepo Structure

```
resto360/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Main CI pipeline
│   │   ├── deploy-staging.yml        # Staging deployment
│   │   ├── deploy-production.yml     # Production deployment
│   │   └── pr-checks.yml             # PR validation
│   ├── CODEOWNERS
│   └── pull_request_template.md
│
├── .planning/                         # GSD planning files
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   ├── STATE.md
│   └── phases/
│
├── apps/
│   ├── api/                          # Django Backend
│   │   ├── config/                   # Django project config
│   │   │   ├── __init__.py
│   │   │   ├── settings/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py           # Shared settings
│   │   │   │   ├── development.py
│   │   │   │   ├── staging.py
│   │   │   │   └── production.py
│   │   │   ├── urls.py
│   │   │   ├── wsgi.py
│   │   │   ├── asgi.py
│   │   │   └── celery.py
│   │   │
│   │   ├── apps/                     # Django apps
│   │   │   ├── core/                 # Shared utilities
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # BaseModel with timestamps
│   │   │   │   ├── managers.py       # TenantManager
│   │   │   │   ├── middleware.py     # TenantMiddleware
│   │   │   │   ├── permissions.py    # Custom DRF permissions
│   │   │   │   ├── pagination.py     # Standard pagination
│   │   │   │   ├── exceptions.py     # Custom exceptions
│   │   │   │   └── utils.py
│   │   │   │
│   │   │   ├── authentication/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # User, Restaurant, Role
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services.py       # Business logic
│   │   │   │   └── tests/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── test_models.py
│   │   │   │       ├── test_views.py
│   │   │   │       └── factories.py
│   │   │   │
│   │   │   ├── pos/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # MenuCategory, MenuItem
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services.py
│   │   │   │   └── tests/
│   │   │   │
│   │   │   ├── orders/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # Order, OrderItem
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services.py
│   │   │   │   ├── signals.py        # Order lifecycle events
│   │   │   │   └── tests/
│   │   │   │
│   │   │   ├── payments/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # Payment, Transaction
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base.py       # PaymentProvider ABC
│   │   │   │   │   ├── wave.py
│   │   │   │   │   ├── orange.py
│   │   │   │   │   ├── mtn.py
│   │   │   │   │   └── cash.py
│   │   │   │   ├── webhooks.py       # Payment callbacks
│   │   │   │   └── tests/
│   │   │   │
│   │   │   ├── delivery/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # Delivery, Driver, Zone
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services.py
│   │   │   │   ├── routing.py        # Driver assignment logic
│   │   │   │   └── tests/
│   │   │   │
│   │   │   ├── whatsapp/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # Conversation, Message
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── message_parser.py
│   │   │   │   │   └── order_builder.py
│   │   │   │   ├── webhooks.py
│   │   │   │   └── tests/
│   │   │   │
│   │   │   ├── suppliers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # Supplier, Product, PurchaseOrder
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services.py
│   │   │   │   └── tests/
│   │   │   │
│   │   │   ├── inventory/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # Stock, StockMovement
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services.py
│   │   │   │   └── tests/
│   │   │   │
│   │   │   ├── finance/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py         # Loan, CashAdvance, Repayment
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── scoring.py    # Credit scoring
│   │   │   │   │   └── disbursement.py
│   │   │   │   └── tests/
│   │   │   │
│   │   │   └── analytics/
│   │   │       ├── __init__.py
│   │   │       ├── models.py         # DailySales, Metrics
│   │   │       ├── serializers.py
│   │   │       ├── views.py
│   │   │       ├── urls.py
│   │   │       ├── aggregators.py    # Report generation
│   │   │       └── tests/
│   │   │
│   │   ├── tasks/                    # Celery tasks
│   │   │   ├── __init__.py
│   │   │   ├── payments.py
│   │   │   ├── notifications.py
│   │   │   ├── analytics.py
│   │   │   └── sync.py
│   │   │
│   │   ├── migrations/               # All migrations
│   │   │
│   │   ├── fixtures/                 # Test data
│   │   │   ├── restaurants.json
│   │   │   ├── menu_items.json
│   │   │   └── test_orders.json
│   │   │
│   │   ├── manage.py
│   │   ├── pytest.ini
│   │   ├── conftest.py               # Shared pytest fixtures
│   │   └── requirements/
│   │       ├── base.txt
│   │       ├── development.txt
│   │       ├── production.txt
│   │       └── testing.txt
│   │
│   ├── pos/                          # Next.js POS Application
│   │   ├── public/
│   │   │   ├── manifest.json         # PWA manifest
│   │   │   ├── sw.js                 # Service worker
│   │   │   └── icons/
│   │   │
│   │   ├── src/
│   │   │   ├── app/                  # Next.js App Router
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx          # Dashboard
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── login/
│   │   │   │   │   └── logout/
│   │   │   │   ├── orders/
│   │   │   │   │   ├── page.tsx      # Order list
│   │   │   │   │   ├── new/
│   │   │   │   │   └── [id]/
│   │   │   │   ├── menu/
│   │   │   │   ├── kitchen/
│   │   │   │   ├── payments/
│   │   │   │   └── settings/
│   │   │   │
│   │   │   ├── components/
│   │   │   │   ├── ui/               # Shadcn/ui components
│   │   │   │   ├── orders/
│   │   │   │   ├── menu/
│   │   │   │   ├── payments/
│   │   │   │   └── layout/
│   │   │   │
│   │   │   ├── hooks/
│   │   │   │   ├── useOfflineSync.ts
│   │   │   │   ├── useOrders.ts
│   │   │   │   └── usePayment.ts
│   │   │   │
│   │   │   ├── lib/
│   │   │   │   ├── api.ts            # API client
│   │   │   │   ├── db.ts             # Dexie.js IndexedDB
│   │   │   │   ├── sync.ts           # Sync manager
│   │   │   │   └── utils.ts
│   │   │   │
│   │   │   ├── stores/               # Zustand stores
│   │   │   │   ├── auth.ts
│   │   │   │   ├── cart.ts
│   │   │   │   └── sync.ts
│   │   │   │
│   │   │   └── types/
│   │   │       └── index.ts
│   │   │
│   │   ├── tests/
│   │   │   ├── components/
│   │   │   └── e2e/                  # Playwright tests
│   │   │
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── mobile/                       # React Native (Expo)
│   │   ├── apps/
│   │   │   ├── customer/             # Customer app
│   │   │   │   ├── app/              # Expo Router
│   │   │   │   ├── components/
│   │   │   │   ├── hooks/
│   │   │   │   ├── stores/
│   │   │   │   ├── app.json
│   │   │   │   └── package.json
│   │   │   │
│   │   │   └── driver/               # Driver app
│   │   │       ├── app/
│   │   │       ├── components/
│   │   │       ├── hooks/
│   │   │       ├── stores/
│   │   │       ├── app.json
│   │   │       └── package.json
│   │   │
│   │   └── packages/
│   │       └── shared/               # Shared RN components
│   │           ├── components/
│   │           ├── hooks/
│   │           └── utils/
│   │
│   └── admin/                        # Admin Dashboard (Next.js)
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   └── lib/
│       ├── next.config.js
│       └── package.json
│
├── packages/                         # Shared packages
│   ├── types/                        # Shared TypeScript types
│   │   ├── src/
│   │   │   ├── models/
│   │   │   │   ├── restaurant.ts
│   │   │   │   ├── order.ts
│   │   │   │   ├── menu.ts
│   │   │   │   ├── payment.ts
│   │   │   │   └── index.ts
│   │   │   ├── api/
│   │   │   │   ├── requests.ts
│   │   │   │   ├── responses.ts
│   │   │   │   └── index.ts
│   │   │   └── index.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── api-client/                   # Generated API client
│   │   ├── src/
│   │   │   ├── client.ts
│   │   │   └── endpoints/
│   │   └── package.json
│   │
│   └── ui/                           # Shared UI components (web)
│       ├── src/
│       └── package.json
│
├── scripts/
│   ├── setup-dev.sh                  # Dev environment setup
│   ├── generate-types.sh             # OpenAPI → TypeScript
│   ├── db-backup.sh
│   ├── db-restore.sh
│   └── seed-data.py
│
├── docs/
│   ├── api/                          # OpenAPI specs
│   │   └── openapi.yaml
│   ├── architecture/
│   │   └── decisions/                # ADRs
│   ├── deployment/
│   └── onboarding/
│
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.pos
│   └── docker-compose.yml            # Local development
│
├── .env.example
├── .gitignore
├── README.md
├── package.json                      # Monorepo root (pnpm workspaces)
├── pnpm-workspace.yaml
├── turbo.json                        # Turborepo config
└── render.yaml                       # Render Blueprint
```

---

## 3. Database Schema Design

### 3.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CORE ENTITIES                                           │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Restaurant    │         │      User       │         │      Role       │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ restaurant_id   │         │ id (PK)         │
│ name            │         │ id (PK)         │────────►│ name            │
│ slug            │         │ email           │         │ permissions[]   │
│ phone           │         │ phone           │         └─────────────────┘
│ address         │         │ password_hash   │
│ timezone        │         │ role_id (FK)    │
│ currency (XOF)  │         │ is_active       │
│ settings (JSON) │         │ language        │
│ plan_id (FK)    │         │ created_at      │
│ is_active       │         │ last_login      │
│ created_at      │         └─────────────────┘
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐         ┌─────────────────┐
│  MenuCategory   │         │    MenuItem     │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ category_id(FK) │
│ restaurant_id   │         │ id (PK)         │
│ name            │         │ restaurant_id   │
│ name_en         │         │ name            │
│ display_order   │         │ name_en         │
│ is_active       │         │ description     │
│ image_url       │         │ price           │
└─────────────────┘         │ image_url       │
                            │ is_available    │
                            │ prep_time_mins  │
                            │ options (JSON)  │
                            └────────┬────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         │                                                       │
         ▼                                                       ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     Order       │         │   OrderItem     │         │    Customer     │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ order_id (FK)   │         │ id (PK)         │
│ restaurant_id   │         │ id (PK)         │         │ restaurant_id   │
│ order_number    │         │ menu_item_id    │◄────────│ phone           │
│ customer_id(FK) │────────►│ quantity        │         │ name            │
│ order_type      │         │ unit_price      │         │ email           │
│ status          │         │ options (JSON)  │         │ address         │
│ subtotal        │         │ notes           │         │ location (GIS)  │
│ tax             │         └─────────────────┘         │ total_orders    │
│ delivery_fee    │                                     │ created_at      │
│ total           │                                     └─────────────────┘
│ source          │
│ notes           │
│ created_by      │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:1
         ▼
┌─────────────────┐         ┌─────────────────┐
│    Payment      │         │  PaymentMethod  │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │
│ order_id (FK)   │         │ name            │
│ restaurant_id   │         │ provider        │
│ method_id (FK)  │────────►│ (wave/orange/   │
│ amount          │         │  mtn/cash)      │
│ currency        │         │ is_active       │
│ status          │         │ config (JSON)   │
│ provider_ref    │         └─────────────────┘
│ idempotency_key │
│ metadata (JSON) │
│ created_at      │
│ confirmed_at    │
└─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DELIVERY ENTITIES                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    Delivery     │         │     Driver      │         │  DeliveryZone   │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │         │ id (PK)         │
│ order_id (FK)   │         │ restaurant_id   │         │ restaurant_id   │
│ restaurant_id   │         │ user_id (FK)    │         │ name            │
│ driver_id (FK)  │────────►│ phone           │         │ polygon (GIS)   │
│ status          │         │ vehicle_type    │         │ delivery_fee    │
│ pickup_address  │         │ is_available    │         │ min_order       │
│ delivery_addr   │         │ current_loc     │         │ is_active       │
│ distance_km     │         │ rating          │         └─────────────────┘
│ estimated_mins  │         │ total_deliveries│
│ picked_up_at    │         └─────────────────┘
│ delivered_at    │
│ customer_rating │
│ driver_notes    │
└─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           SUPPLIER/INVENTORY ENTITIES                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    Supplier     │         │ SupplierProduct │         │  PurchaseOrder  │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ supplier_id(FK) │         │ id (PK)         │
│ name            │         │ id (PK)         │◄────────│ restaurant_id   │
│ contact_name    │         │ name            │         │ supplier_id(FK) │
│ phone           │         │ sku             │         │ status          │
│ email           │         │ unit            │         │ total           │
│ address         │         │ price           │         │ ordered_at      │
│ categories[]    │         │ min_quantity    │         │ delivered_at    │
│ is_verified     │         │ lead_time_days  │         │ notes           │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                     │
                                     │
                                     ▼
┌─────────────────┐         ┌─────────────────┐
│   StockItem     │         │  StockMovement  │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ stock_item_id   │
│ restaurant_id   │         │ id (PK)         │
│ name            │         │ quantity        │
│ sku             │         │ movement_type   │
│ current_qty     │         │ (in/out/adjust) │
│ min_qty         │         │ reference_id    │
│ unit            │         │ notes           │
│ last_restocked  │         │ created_at      │
└─────────────────┘         │ created_by      │
                            └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FINANCE ENTITIES                                        │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│      Loan       │         │   Repayment     │         │  CashAdvance    │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ loan_id (FK)    │         │ id (PK)         │
│ restaurant_id   │         │ id (PK)         │         │ restaurant_id   │
│ amount          │         │ amount          │         │ amount          │
│ interest_rate   │         │ payment_date    │         │ fee_percent     │
│ term_months     │         │ status          │         │ repay_percent   │
│ monthly_payment │         │ payment_method  │         │ status          │
│ status          │         └─────────────────┘         │ disbursed_at    │
│ disbursed_at    │                                     │ repaid_at       │
│ due_date        │                                     │ balance         │
│ credit_score    │                                     └─────────────────┘
└─────────────────┘
```

### 3.2 Key Indexes

```sql
-- Performance indexes for high-traffic queries

-- Orders: Most queried table
CREATE INDEX idx_orders_restaurant_status ON orders(restaurant_id, status);
CREATE INDEX idx_orders_restaurant_created ON orders(restaurant_id, created_at DESC);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_order_number ON orders(restaurant_id, order_number);

-- Payments: Status checks and reconciliation
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_provider_ref ON payments(provider_ref);
CREATE INDEX idx_payments_idempotency ON payments(idempotency_key);

-- Menu items: Frequent lookups
CREATE INDEX idx_menu_items_restaurant ON menu_items(restaurant_id, is_available);
CREATE INDEX idx_menu_items_category ON menu_items(category_id);

-- Customers: Phone lookup (WhatsApp integration)
CREATE INDEX idx_customers_phone ON customers(restaurant_id, phone);

-- Deliveries: Active delivery tracking
CREATE INDEX idx_deliveries_driver_status ON deliveries(driver_id, status);
CREATE INDEX idx_deliveries_restaurant_status ON deliveries(restaurant_id, status);

-- Drivers: Availability queries
CREATE INDEX idx_drivers_available ON drivers(restaurant_id, is_available);

-- Analytics: Date-based aggregations
CREATE INDEX idx_orders_date ON orders(restaurant_id, DATE(created_at));
```

### 3.3 Django Models (Core Examples)

```python
# apps/core/models.py
from django.db import models
from django.utils import timezone
import uuid

class BaseModel(models.Model):
    """Abstract base for all tenant models."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(BaseModel):
    """Abstract base for tenant-scoped models."""
    restaurant = models.ForeignKey(
        'authentication.Restaurant',
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )

    class Meta:
        abstract = True


# apps/orders/models.py
class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    PREPARING = 'preparing', 'Preparing'
    READY = 'ready', 'Ready'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class OrderType(models.TextChoices):
    DINE_IN = 'dine_in', 'Dine In'
    TAKEOUT = 'takeout', 'Takeout'
    DELIVERY = 'delivery', 'Delivery'


class OrderSource(models.TextChoices):
    POS = 'pos', 'POS'
    WHATSAPP = 'whatsapp', 'WhatsApp'
    CUSTOMER_APP = 'customer_app', 'Customer App'
    WEBSITE = 'website', 'Website'


class Order(TenantModel):
    order_number = models.CharField(max_length=20)  # e.g., "R001-20240203-0042"
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    order_type = models.CharField(max_length=20, choices=OrderType.choices)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    source = models.CharField(max_length=20, choices=OrderSource.choices)

    subtotal = models.DecimalField(max_digits=10, decimal_places=0)  # XOF has no decimals
    tax = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=0)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True
    )

    # Offline sync support
    local_id = models.UUIDField(null=True, blank=True)  # Client-generated UUID
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['restaurant', '-created_at']),
            models.Index(fields=['order_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'order_number'],
                name='unique_order_number_per_restaurant'
            )
        ]

    def generate_order_number(self):
        """Generate order number: R{restaurant_short}-{date}-{sequence}"""
        from django.db.models import Max
        today = timezone.now().date()
        prefix = f"R{self.restaurant.id.hex[:3].upper()}-{today.strftime('%Y%m%d')}"

        last_order = Order.objects.filter(
            restaurant=self.restaurant,
            order_number__startswith=prefix
        ).aggregate(Max('order_number'))

        if last_order['order_number__max']:
            last_seq = int(last_order['order_number__max'].split('-')[-1])
            seq = last_seq + 1
        else:
            seq = 1

        return f"{prefix}-{seq:04d}"
```

---

## 4. API Design Principles

### 4.1 REST Conventions

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              API CONVENTIONS                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

BASE URL: https://api.resto360.ci/v1/

RESOURCE NAMING:
  ✓ Plural nouns: /orders, /menu-items, /payments
  ✓ Kebab-case: /menu-items (not menuItems or menu_items)
  ✓ Nested for relationships: /orders/{id}/items

HTTP METHODS:
  GET    /orders          → List orders (paginated)
  GET    /orders/{id}     → Get single order
  POST   /orders          → Create order
  PATCH  /orders/{id}     → Partial update
  DELETE /orders/{id}     → Soft delete (set is_active=false)

FILTERING:
  GET /orders?status=pending&created_after=2024-02-01

SORTING:
  GET /orders?sort=-created_at (- prefix for descending)

SEARCH:
  GET /menu-items?search=poulet

INCLUDES (sparse fieldsets):
  GET /orders?include=items,customer,payment
```

### 4.2 Authentication Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           JWT AUTHENTICATION FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘

1. LOGIN
   POST /auth/login
   {
     "phone": "+2250701234567",
     "password": "..."
   }

   Response:
   {
     "access_token": "eyJ...",      // 15 min expiry
     "refresh_token": "eyJ...",     // 7 days expiry
     "user": {
       "id": "uuid",
       "name": "Koné Amadou",
       "role": "manager",
       "restaurant": {
         "id": "uuid",
         "name": "Maquis Chez Tata"
       }
     }
   }

2. AUTHENTICATED REQUESTS
   Authorization: Bearer eyJ...

3. TOKEN REFRESH
   POST /auth/refresh
   {
     "refresh_token": "eyJ..."
   }

4. LOGOUT
   POST /auth/logout
   (Invalidates refresh token)

TOKEN PAYLOAD:
{
  "sub": "user-uuid",
  "restaurant_id": "restaurant-uuid",
  "role": "manager",
  "permissions": ["orders.create", "orders.read", ...],
  "exp": 1707000000,
  "iat": 1706999100
}
```

### 4.3 Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "phone",
        "message": "Phone number must start with +225"
      }
    ],
    "request_id": "req_abc123",
    "timestamp": "2024-02-03T10:30:00Z"
  }
}

ERROR CODES:
  400 → VALIDATION_ERROR, INVALID_REQUEST
  401 → UNAUTHORIZED, TOKEN_EXPIRED
  403 → FORBIDDEN, INSUFFICIENT_PERMISSIONS
  404 → NOT_FOUND, RESOURCE_NOT_FOUND
  409 → CONFLICT, DUPLICATE_ENTRY
  422 → UNPROCESSABLE_ENTITY
  429 → RATE_LIMIT_EXCEEDED
  500 → INTERNAL_ERROR
  503 → SERVICE_UNAVAILABLE
```

### 4.4 Pagination

```json
GET /orders?page=2&per_page=20

Response:
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 156,
    "total_pages": 8,
    "has_next": true,
    "has_prev": true
  },
  "links": {
    "self": "/v1/orders?page=2&per_page=20",
    "first": "/v1/orders?page=1&per_page=20",
    "prev": "/v1/orders?page=1&per_page=20",
    "next": "/v1/orders?page=3&per_page=20",
    "last": "/v1/orders?page=8&per_page=20"
  }
}
```

### 4.5 API Versioning

```
URL Path Versioning: /v1/, /v2/

STRATEGY:
- Major versions only (v1, v2)
- Deprecation period: 6 months
- Sunset header for deprecated endpoints:
  Sunset: Sat, 01 Jun 2025 00:00:00 GMT
  Deprecation: true

VERSION NEGOTIATION:
- Primary: URL path (/v1/orders)
- Fallback: Accept header (Accept: application/vnd.resto360.v1+json)
```

---

## 5. Development Workflow

### 5.1 Git Branching Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              BRANCHING MODEL                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

main ─────────────────────────────────────────────────────────────► (production)
  │                                                    ▲
  │                                                    │ merge
  │                                                    │
develop ──────────────────────────────────────────────┴──────────► (staging)
  │         │         │
  │         │         └── feature/whatsapp-orders ────┐
  │         │                                         │ PR
  │         └── feature/wave-payment ─────────────────┤
  │                                                   │
  └── feature/pos-offline-sync ───────────────────────┘


BRANCH NAMING:
  feature/*     New features (feature/pos-offline-sync)
  fix/*         Bug fixes (fix/payment-timeout)
  hotfix/*      Production hotfixes (hotfix/critical-payment-bug)
  refactor/*    Code refactoring (refactor/order-service)
  docs/*        Documentation (docs/api-endpoints)

COMMIT MESSAGE FORMAT (Conventional Commits):
  feat(orders): add offline order creation
  fix(payments): handle Wave timeout correctly
  docs(api): update authentication endpoints
  test(pos): add offline sync integration tests
  refactor(core): extract tenant middleware
```

### 5.2 PR Review Process

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PR CHECKLIST                                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

BEFORE CREATING PR:
  □ Tests pass locally (pytest)
  □ Linting passes (ruff, eslint)
  □ Types check (mypy, tsc)
  □ Self-reviewed diff
  □ Rebased on develop

PR REQUIREMENTS:
  □ Descriptive title (feat: add Wave payment integration)
  □ Description with context
  □ Screenshots for UI changes
  □ Test coverage for new code
  □ No secrets in code
  □ API docs updated if endpoints changed

REVIEW CRITERIA:
  □ Code is readable and maintainable
  □ Tests are meaningful (not just coverage padding)
  □ Error handling is complete
  □ Security considerations addressed
  □ Performance implications considered

MERGE REQUIREMENTS:
  □ At least 1 approval
  □ All CI checks pass
  □ No merge conflicts
  □ Squash merge to develop
```

### 5.3 TDD Cycle

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              TDD WORKFLOW                                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │             │
    │    RED      │◄──── 1. Write failing test
    │             │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │             │
    │   GREEN     │◄──── 2. Write minimum code to pass
    │             │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │             │
    │  REFACTOR   │◄──── 3. Clean up, keep tests green
    │             │
    └──────┬──────┘
           │
           └───────────► Repeat


EXAMPLE FLOW (Order Creation):

1. RED - Write test first:
   ```python
   def test_create_order_success(self, api_client, restaurant, menu_item):
       response = api_client.post('/v1/orders/', {
           'order_type': 'dine_in',
           'items': [{'menu_item_id': str(menu_item.id), 'quantity': 2}]
       })
       assert response.status_code == 201
       assert response.data['order_number'] is not None
   ```

2. GREEN - Implement minimum:
   ```python
   class OrderViewSet(viewsets.ModelViewSet):
       def create(self, request):
           # Just enough to pass the test
           ...
   ```

3. REFACTOR - Clean up:
   - Extract order number generation
   - Add validation
   - Keep all tests green
```

### 5.4 CI/CD Pipeline Stages

```yaml
# .github/workflows/ci.yml

name: CI Pipeline

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop]

jobs:
  # Stage 1: Code Quality
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Linting
        run: |
          pip install ruff
          ruff check apps/api/
      - name: TypeScript Linting
        run: |
          pnpm install
          pnpm lint

  # Stage 2: Type Checking
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Types
        run: |
          pip install mypy
          mypy apps/api/
      - name: TypeScript Types
        run: |
          pnpm install
          pnpm typecheck

  # Stage 3: Unit Tests
  test-unit:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: resto360_test
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - name: Run API Tests
        run: |
          cd apps/api
          pip install -r requirements/testing.txt
          pytest --cov=apps --cov-report=xml
      - name: Run Frontend Tests
        run: |
          pnpm install
          pnpm test

  # Stage 4: Integration Tests
  test-integration:
    needs: [lint, typecheck, test-unit]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: API Integration Tests
        run: |
          docker-compose -f docker/docker-compose.test.yml up -d
          pytest tests/integration/

  # Stage 5: E2E Tests (on develop/main only)
  test-e2e:
    if: github.ref == 'refs/heads/develop' || github.ref == 'refs/heads/main'
    needs: [test-integration]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Playwright Tests
        run: |
          pnpm install
          pnpm exec playwright install
          pnpm test:e2e

  # Stage 6: Build
  build:
    needs: [test-unit]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker Images
        run: |
          docker build -f docker/Dockerfile.api -t resto360-api .
          docker build -f docker/Dockerfile.pos -t resto360-pos .
```

---

## 6. Security Architecture

### 6.1 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              SECURITY LAYERS                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

Layer 1: TRANSPORT
  • TLS 1.3 everywhere
  • HSTS enabled
  • Certificate pinning in mobile apps

Layer 2: AUTHENTICATION
  • JWT with short expiry (15 min access, 7 day refresh)
  • Phone-based login (SMS OTP for initial registration)
  • Password hashing with Argon2id
  • Brute force protection (5 attempts, 15 min lockout)

Layer 3: AUTHORIZATION
  • Role-Based Access Control (RBAC)
  • Permission-based API access
  • Tenant isolation at query level

Layer 4: INPUT VALIDATION
  • Schema validation on all inputs
  • SQL injection prevention (ORM)
  • XSS prevention (content sanitization)

ROLES & PERMISSIONS:
┌─────────────┬──────────────────────────────────────────────────────────────────────┐
│ Role        │ Permissions                                                          │
├─────────────┼──────────────────────────────────────────────────────────────────────┤
│ owner       │ All permissions + restaurant settings + billing + staff management  │
│ manager     │ Orders, menu, inventory, reports, staff (no billing)                │
│ cashier     │ Orders (create, view), payments (create)                            │
│ kitchen     │ Orders (view, update status)                                        │
│ driver      │ Deliveries (view assigned, update status)                           │
│ customer    │ Own orders only (view, create via app)                              │
└─────────────┴──────────────────────────────────────────────────────────────────────┘
```

### 6.2 Payment Data Handling

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           PAYMENT SECURITY (PCI-DSS Lite)                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

PRINCIPLE: We NEVER store card data. Mobile money only.

MOBILE MONEY FLOW:
1. Customer initiates payment (Wave/Orange/MTN)
2. We send request to provider API with:
   - Amount
   - Phone number
   - Our merchant ID
   - Callback URL
3. Provider sends push to customer phone
4. Customer approves on their phone
5. Provider sends webhook to our callback
6. We update payment status

WHAT WE STORE:
  ✓ Transaction reference (provider's ID)
  ✓ Amount and currency
  ✓ Status (pending, success, failed)
  ✓ Timestamp
  ✗ Never store: PINs, OTPs, or any auth data

WEBHOOK SECURITY:
  • Signature verification (HMAC-SHA256)
  • IP allowlisting for provider IPs
  • Idempotency handling
  • Async processing (queue, don't block)

SECRETS MANAGEMENT:
  • API keys in environment variables
  • Render's secret management
  • Never in code or logs
```

### 6.3 Rate Limiting Strategy

```python
# DRF Throttling Configuration

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Authentication endpoints (prevent brute force)
        'auth': '5/minute',

        # Payment endpoints (prevent abuse)
        'payments': '10/minute',

        # Order creation (legitimate high traffic)
        'orders': '60/minute',

        # General API access
        'default': '100/minute',

        # Webhooks (from payment providers)
        'webhooks': '200/minute',
    }
}

# Per-endpoint throttle scope
class PaymentViewSet(viewsets.ModelViewSet):
    throttle_scope = 'payments'

# Additional Cloudflare WAF rules:
# - Block known bad IPs
# - Challenge suspicious traffic patterns
# - DDoS protection
```

---

## 7. Testing Strategy

### 7.1 Test Pyramid

```
                          ┌───────────────┐
                          │     E2E       │  ~10%
                          │  (Playwright) │  Critical user journeys
                          └───────┬───────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │       Integration         │  ~30%
                    │      (API Tests)          │  Endpoint behavior
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        │                      Unit                         │  ~60%
        │              (pytest + Jest)                      │  Business logic
        └───────────────────────────────────────────────────┘
```

### 7.2 Test Examples

```python
# Unit Test (apps/orders/tests/test_services.py)
import pytest
from apps.orders.services import OrderService
from apps.orders.factories import MenuItemFactory

class TestOrderService:
    @pytest.fixture
    def order_service(self, restaurant):
        return OrderService(restaurant=restaurant)

    def test_calculate_total_with_tax(self, order_service):
        items = [
            {'menu_item_id': 'uuid', 'quantity': 2, 'unit_price': 5000},
            {'menu_item_id': 'uuid', 'quantity': 1, 'unit_price': 3000},
        ]
        total = order_service.calculate_total(items)
        assert total == 13000  # (2*5000 + 1*3000)

    def test_calculate_total_with_delivery_fee(self, order_service):
        items = [{'menu_item_id': 'uuid', 'quantity': 1, 'unit_price': 5000}]
        total = order_service.calculate_total(items, delivery_fee=1500)
        assert total == 6500


# Integration Test (tests/integration/test_orders_api.py)
import pytest
from rest_framework.test import APIClient

class TestOrdersAPI:
    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_create_order_success(self, api_client, restaurant, menu_item):
        response = api_client.post('/v1/orders/', {
            'order_type': 'dine_in',
            'items': [
                {'menu_item_id': str(menu_item.id), 'quantity': 2}
            ]
        })

        assert response.status_code == 201
        assert response.data['status'] == 'pending'
        assert response.data['total'] == menu_item.price * 2

    def test_create_order_unauthenticated(self, restaurant):
        client = APIClient()
        response = client.post('/v1/orders/', {'order_type': 'dine_in'})
        assert response.status_code == 401


# E2E Test (apps/pos/tests/e2e/order-flow.spec.ts)
import { test, expect } from '@playwright/test';

test.describe('Order Creation Flow', () => {
  test('cashier can create dine-in order', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="phone"]', '+2250701234567');
    await page.fill('[name="password"]', 'testpass');
    await page.click('button[type="submit"]');

    // Navigate to new order
    await page.click('text=Nouvelle Commande');

    // Add items
    await page.click('[data-item="poulet-braise"]');
    await page.click('[data-item="poulet-braise"]');
    await page.click('[data-item="alloco"]');

    // Verify cart
    await expect(page.locator('[data-testid="cart-total"]')).toContainText('13,000 XOF');

    // Submit order
    await page.click('button:has-text("Commander")');

    // Verify success
    await expect(page.locator('[data-testid="order-confirmation"]')).toBeVisible();
  });
});
```

### 7.3 Mock Strategy for External APIs

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_wave_api():
    """Mock Wave payment API responses."""
    with patch('apps.payments.services.wave.WaveClient') as mock:
        instance = mock.return_value
        instance.create_payment.return_value = {
            'id': 'wave_txn_123',
            'status': 'pending',
            'checkout_url': 'https://wave.com/pay/123'
        }
        instance.check_status.return_value = {
            'id': 'wave_txn_123',
            'status': 'success'
        }
        yield instance

@pytest.fixture
def mock_orange_api():
    """Mock Orange Money API responses."""
    with patch('apps.payments.services.orange.OrangeClient') as mock:
        instance = mock.return_value
        instance.initiate_payment.return_value = {
            'transaction_id': 'orange_123',
            'ussd_code': '*144*4*1#'
        }
        yield instance

# Usage in tests
def test_wave_payment_success(api_client, order, mock_wave_api):
    response = api_client.post(f'/v1/orders/{order.id}/pay/', {
        'method': 'wave',
        'phone': '+2250701234567'
    })

    assert response.status_code == 200
    assert response.data['payment_status'] == 'pending'
    mock_wave_api.create_payment.assert_called_once()
```

### 7.4 Coverage Targets

```
┌────────────────────────┬──────────────┬─────────────────────────────────────────────┐
│ Component              │ Target       │ Notes                                       │
├────────────────────────┼──────────────┼─────────────────────────────────────────────┤
│ Payment Services       │ 95%          │ Critical path - highest coverage            │
│ Order Services         │ 90%          │ Core business logic                         │
│ API Views              │ 85%          │ All endpoints tested                        │
│ Models                 │ 80%          │ Validation, computed properties             │
│ Frontend Components    │ 75%          │ User interactions, edge cases               │
│ Utilities              │ 70%          │ Shared helpers                              │
│ Overall                │ 80%          │ Minimum for merge to develop                │
└────────────────────────┴──────────────┴─────────────────────────────────────────────┘
```

---

## 8. Deployment Architecture

### 8.1 Render Services Setup

```yaml
# render.yaml (Infrastructure as Code)

services:
  # Main API
  - type: web
    name: resto360-api
    runtime: python
    buildCommand: |
      pip install -r apps/api/requirements/production.txt
      python apps/api/manage.py collectstatic --noinput
    startCommand: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
      - key: DATABASE_URL
        fromDatabase:
          name: resto360-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: resto360-redis
          type: redis
          property: connectionString
      - fromGroup: resto360-secrets
    healthCheckPath: /health/
    autoDeploy: true

  # Celery Workers
  - type: worker
    name: resto360-worker
    runtime: python
    buildCommand: pip install -r apps/api/requirements/production.txt
    startCommand: celery -A config worker -l info --concurrency 4
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
      - fromGroup: resto360-secrets

  # Celery Beat (Scheduler)
  - type: worker
    name: resto360-beat
    runtime: python
    buildCommand: pip install -r apps/api/requirements/production.txt
    startCommand: celery -A config beat -l info
    envVars:
      - fromGroup: resto360-secrets

  # POS Frontend
  - type: web
    name: resto360-pos
    runtime: static
    buildCommand: pnpm install && pnpm build:pos
    staticPublishPath: apps/pos/out
    headers:
      - path: /*
        name: Cache-Control
        value: public, max-age=31536000, immutable
    routes:
      - type: rewrite
        source: /*
        destination: /index.html

databases:
  - name: resto360-db
    databaseName: resto360
    postgresMajorVersion: 15
    plan: standard  # Upgrade as needed

envVarGroups:
  - name: resto360-secrets
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: WAVE_API_KEY
        sync: false
      - key: ORANGE_API_KEY
        sync: false
      - key: MTN_API_KEY
        sync: false
      - key: SENTRY_DSN
        sync: false
```

### 8.2 Environment Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ENVIRONMENTS                                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

DEVELOPMENT (Local)
  • Docker Compose for all services
  • SQLite or local Postgres
  • Mock payment providers
  • Hot reload enabled

STAGING (Render - Auto-deploy from develop)
  • Separate Render project
  • Sandbox payment APIs
  • Same architecture as production
  • Used for integration testing
  • Test data (fake restaurants)

PRODUCTION (Render - Manual deploy from main)
  • Production Render project
  • Live payment APIs
  • Real customer data
  • Monitoring enabled
  • Daily backups


ENVIRONMENT VARIABLES:
┌─────────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Variable            │ Development     │ Staging         │ Production      │
├─────────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ DEBUG               │ True            │ False           │ False           │
│ ALLOWED_HOSTS       │ localhost       │ staging.resto   │ api.resto360.ci │
│ WAVE_API_URL        │ mock            │ sandbox.wave    │ api.wave.com    │
│ SENTRY_ENVIRONMENT  │ (none)          │ staging         │ production      │
│ LOG_LEVEL           │ DEBUG           │ INFO            │ WARNING         │
└─────────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### 8.3 Database Migration Strategy

```python
# Safe migration practices

# 1. BACKWARD COMPATIBLE CHANGES
# Add new columns as nullable or with defaults
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='order',
            name='priority',
            field=models.CharField(max_length=20, null=True),  # Nullable first
        ),
    ]

# 2. MULTI-STEP SCHEMA CHANGES
# Step 1: Add new column (nullable)
# Step 2: Backfill data
# Step 3: Make non-nullable (separate deploy)

# 3. ZERO-DOWNTIME RENAMES
# Never rename columns directly. Instead:
# a) Add new column
# b) Copy data
# c) Update code to use new column
# d) Remove old column (later deploy)

# 4. MIGRATION COMMANDS
# Development:
#   python manage.py makemigrations
#   python manage.py migrate

# Production (via Render):
#   Migrations run automatically on deploy via release command:
#   python manage.py migrate --noinput
```

### 8.4 Zero-Downtime Deployment

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT SEQUENCE                                          │
└─────────────────────────────────────────────────────────────────────────────────────┘

1. PR merged to main
         │
         ▼
2. GitHub Actions: Build & Test
         │
         ▼
3. Manual approval (production deploy)
         │
         ▼
4. Render: Build new image
         │
         ▼
5. Render: Run release command (migrations)
         │
         ▼
6. Render: Start new instances
         │
         ▼
7. Render: Health check passes
         │
         ▼
8. Render: Route traffic to new instances
         │
         ▼
9. Render: Drain old instances
         │
         ▼
10. Deploy complete


ROLLBACK PROCEDURE:
1. Revert commit in main
2. Push revert
3. Render auto-deploys previous version
4. If DB migration issue: Run reverse migration manually
```

---

## 9. 12-Week Build Phases

### 9.1 Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         12-WEEK BUILD TIMELINE                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

Week  1  2  3  4  5  6  7  8  9  10 11 12
      ├──┴──┼──┴──┼──┴──┼──┴──┼──┴──┼──┴──┤
      │     │     │     │     │     │     │
      │FOUND│ PAY │DELIV│WHATS│MARKT│FINAN│
      │+POS │MENTS│ ERY │ APP │PLACE│ CE  │
      │     │     │     │     │     │     │
      └─────┴─────┴─────┴─────┴─────┴─────┘
        M1    M2    M3    M4    M5    M6
```

### 9.2 Detailed Milestone Breakdown

---

#### **MILESTONE 1: Foundation + POS Core (Weeks 1-2)**

**Goal:** Working POS that can take orders (no payments yet)

**Week 1: Foundation**
- [ ] Project scaffolding (monorepo, Django, Next.js)
- [ ] Database schema v1 (restaurants, users, menu, orders)
- [ ] Authentication system (JWT, roles, permissions)
- [ ] Multi-tenancy middleware
- [ ] CI/CD pipeline setup
- [ ] Development environment (Docker Compose)

**Week 2: POS Core**
- [ ] Menu management API (CRUD categories, items)
- [ ] Order creation API (items, notes, order types)
- [ ] POS frontend: Login screen
- [ ] POS frontend: Menu display grid
- [ ] POS frontend: Cart management
- [ ] POS frontend: Order submission
- [ ] Kitchen display view (order queue)

**Deliverable:** Cashier can log in, see menu, create orders, kitchen sees queue

---

#### **MILESTONE 2: Payment Processing (Weeks 3-4)**

**Goal:** Accept Wave, Orange, MTN, and Cash payments

**Week 3: Payment Infrastructure**
- [ ] Payment model and state machine
- [ ] Payment provider abstraction (base class)
- [ ] Wave integration (API client, create payment, webhook)
- [ ] Orange Money integration
- [ ] MTN MoMo integration
- [ ] Idempotency handling

**Week 4: Payment UX**
- [ ] POS: Payment method selection
- [ ] POS: Cash payment flow (drawer management)
- [ ] POS: Mobile money flow (show QR/USSD, wait for confirmation)
- [ ] Payment status polling
- [ ] Receipt generation (PDF)
- [ ] Daily reconciliation report

**Deliverable:** Complete order → payment → receipt flow for all 4 methods

---

#### **MILESTONE 3: Delivery Management (Weeks 5-6)**

**Goal:** Restaurant can manage delivery orders with driver tracking

**Week 5: Delivery Backend**
- [ ] Delivery zones (polygon-based)
- [ ] Driver management (CRUD, availability toggle)
- [ ] Delivery assignment algorithm (nearest available)
- [ ] Real-time location tracking (WebSocket)
- [ ] Delivery status state machine

**Week 6: Mobile Apps Foundation**
- [ ] React Native (Expo) project setup
- [ ] Driver app: Login
- [ ] Driver app: Active deliveries list
- [ ] Driver app: Navigation to address
- [ ] Driver app: Status updates (picked up, delivered)
- [ ] Customer app: Order tracking (map view)

**Deliverable:** Delivery order → driver assigned → real-time tracking → delivered

---

#### **MILESTONE 4: WhatsApp Integration (Weeks 7-8)**

**Goal:** Customers can order via WhatsApp

**Week 7: WhatsApp Infrastructure**
- [ ] Choose provider (Meta Business API vs Twilio) — **DECISION NEEDED**
- [ ] Webhook receiver for incoming messages
- [ ] Message parser (intent detection)
- [ ] Conversation state machine
- [ ] Menu display via WhatsApp (catalog or text)

**Week 8: WhatsApp Order Flow**
- [ ] Order builder from conversation
- [ ] Location capture for delivery
- [ ] Payment link generation
- [ ] Order confirmation messages
- [ ] Status update notifications
- [ ] Customer app: Order history

**Deliverable:** WhatsApp → order → payment link → delivery tracking via WhatsApp

**WhatsApp Integration Options:**

| Option | Pros | Cons |
|--------|------|------|
| **Meta Business API** | Official, reliable, higher limits | Requires approval, monthly fees (~$1k+), complex setup |
| **Twilio for WhatsApp** | Faster setup, good docs, pay-per-message | Higher per-message cost, still needs Meta approval |

**Recommendation:** Start with Twilio for faster MVP, migrate to direct Meta if volume justifies.

---

#### **MILESTONE 5: Supplier Marketplace (Weeks 9-10)**

**Goal:** Restaurants can order supplies from verified suppliers

**Week 9: Inventory System**
- [ ] Stock item management
- [ ] Stock movement tracking (in/out/adjustment)
- [ ] Low stock alerts
- [ ] Menu item → ingredient mapping (optional)
- [ ] Inventory reports

**Week 10: Supplier Platform**
- [ ] Supplier registration and verification
- [ ] Product catalog (per supplier)
- [ ] Purchase order creation
- [ ] Order status tracking
- [ ] Delivery scheduling
- [ ] Invoice management

**Deliverable:** Restaurant sees low stock → orders from supplier → receives delivery

---

#### **MILESTONE 6: Embedded Finance + Polish (Weeks 11-12)**

**Goal:** Business loans and cash advances; production-ready polish

**Week 11: Embedded Finance**
- [ ] Sales data aggregation (daily/weekly/monthly)
- [ ] Credit scoring model (based on sales history)
- [ ] Loan application flow
- [ ] Loan approval workflow
- [ ] Disbursement (via mobile money)
- [ ] Repayment collection (% of daily sales)
- [ ] Cash advance (simpler product)

**Week 12: Production Polish**
- [ ] POS offline mode (IndexedDB sync)
- [ ] Comprehensive error handling
- [ ] Loading states and optimistic updates
- [ ] French translations (i18n complete)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation
- [ ] Production deployment

**Deliverable:** Restaurant applies for loan → instant decision → funds disbursed → auto-repayment

---

### 9.3 Success Metrics per Milestone

| Milestone | Key Metric | Target |
|-----------|------------|--------|
| M1: Foundation | Orders created | 100+ test orders |
| M2: Payments | Payment success rate | >95% |
| M3: Delivery | Delivery completion rate | >90% |
| M4: WhatsApp | Orders via WhatsApp | 50+ in test week |
| M5: Marketplace | Supplier orders placed | 20+ in test week |
| M6: Finance | Loan applications | 5+ pilot restaurants |

---

## Appendix A: WhatsApp Integration Decision Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    WHATSAPP PROVIDER COMPARISON                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

                        Meta Business API          Twilio for WhatsApp
                        ─────────────────          ───────────────────
Setup time              2-4 weeks (approval)       3-5 days
Monthly base cost       ~$0 (+ hosting)            ~$150 base
Per-message cost        $0.005-0.08                $0.005-0.08 + markup
Message limits          Unlimited (approved)       Based on plan
Template approval       Direct with Meta           Via Twilio
API complexity          Higher                     Lower (better docs)
Support                 Limited                    Good (paid plans)

RECOMMENDATION FOR RESTO360:
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│   Phase 1 (MVP):     Twilio for WhatsApp                                            │
│                      • Faster to market                                              │
│                      • Good documentation                                            │
│                      • Predictable pricing for low volume                           │
│                                                                                      │
│   Phase 2 (Scale):   Evaluate Meta Business API                                     │
│                      • When >10,000 messages/month                                   │
│                      • When needing catalog integration                              │
│                      • Build abstraction layer now to enable switch                 │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Quick Reference

### API Endpoints Summary

```
/v1/auth/
  POST   /login                    # Get tokens
  POST   /refresh                  # Refresh access token
  POST   /logout                   # Invalidate refresh token

/v1/restaurants/
  GET    /                         # List (admin only)
  GET    /current                  # Current restaurant details
  PATCH  /current                  # Update settings

/v1/menu-categories/
  GET    /                         # List categories
  POST   /                         # Create category
  PATCH  /{id}                     # Update category
  DELETE /{id}                     # Delete category

/v1/menu-items/
  GET    /                         # List items
  POST   /                         # Create item
  PATCH  /{id}                     # Update item
  DELETE /{id}                     # Delete item

/v1/orders/
  GET    /                         # List orders
  POST   /                         # Create order
  GET    /{id}                     # Get order details
  PATCH  /{id}                     # Update order
  POST   /{id}/pay                 # Initiate payment
  POST   /{id}/cancel              # Cancel order

/v1/payments/
  GET    /                         # List payments
  GET    /{id}                     # Payment details
  POST   /webhooks/wave            # Wave callback
  POST   /webhooks/orange          # Orange callback
  POST   /webhooks/mtn             # MTN callback

/v1/deliveries/
  GET    /                         # List deliveries
  GET    /{id}                     # Delivery details
  PATCH  /{id}                     # Update status
  POST   /{id}/assign              # Assign driver

/v1/drivers/
  GET    /                         # List drivers
  POST   /                         # Create driver
  PATCH  /{id}                     # Update driver
  POST   /{id}/toggle-availability # Toggle online status

/v1/analytics/
  GET    /sales/daily              # Daily sales summary
  GET    /sales/items              # Item popularity
  GET    /orders/stats             # Order statistics
```

### Key Commands

```bash
# Development
docker-compose up                    # Start all services
pnpm dev                             # Start frontend dev servers
pytest                               # Run all tests
pytest --cov=apps                    # With coverage

# Database
python manage.py makemigrations      # Create migrations
python manage.py migrate             # Apply migrations
python manage.py createsuperuser     # Create admin user

# Code Quality
ruff check apps/api/                 # Python linting
pnpm lint                            # TypeScript linting
pnpm typecheck                       # Type checking

# Deployment
git push origin develop              # Deploy to staging
git push origin main                 # Deploy to production (after approval)
```

---

*Document Version: 1.0*
*Last Updated: 2026-02-03*
*Next Review: After Milestone 1 completion*
