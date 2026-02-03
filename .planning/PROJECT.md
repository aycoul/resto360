# RESTO360

## What This Is

RESTO360 is an enterprise-grade Restaurant Operating System for Côte d'Ivoire and West Africa. It's a comprehensive multi-tenant SaaS platform that handles point-of-sale, mobile money payments (Wave, Orange, MTN), delivery management, WhatsApp ordering, supplier marketplace, and embedded business financing — all designed for the realities of West African infrastructure (offline-first, mobile money primary).

## Core Value

Restaurants can take orders, accept payments, and manage deliveries — even when internet is unreliable.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**POS Core**
- [ ] Tablet-based POS with offline-first capability
- [ ] Menu management (categories, items, pricing, availability)
- [ ] Order creation (dine-in, takeout, delivery)
- [ ] Kitchen display for order queue
- [ ] Receipt generation

**Payment Processing**
- [ ] Wave Money integration (direct API)
- [ ] Orange Money integration (direct API)
- [ ] MTN MoMo integration (direct API)
- [ ] Cash payment tracking
- [ ] Payment reconciliation reports

**Delivery Management**
- [ ] Delivery zone configuration
- [ ] Driver management and assignment
- [ ] Real-time order tracking
- [ ] Customer delivery app
- [ ] Driver mobile app

**WhatsApp Integration**
- [ ] Receive orders via WhatsApp
- [ ] Menu browsing in chat
- [ ] Order status notifications
- [ ] Payment link generation

**Supplier Marketplace**
- [ ] Inventory/stock management
- [ ] Low stock alerts
- [ ] Supplier catalog browsing
- [ ] Purchase order creation
- [ ] Delivery tracking

**Embedded Finance**
- [ ] Sales-based credit scoring
- [ ] Business loan applications
- [ ] Cash advance product
- [ ] Automated repayment collection

### Out of Scope

- Card payments (Visa/Mastercard) — mobile money is primary in target market
- Multi-country (v1 is Côte d'Ivoire only) — expand after validation
- Native iOS/Android POS apps — PWA sufficient for tablets
- Real-time chat support — WhatsApp handles customer communication
- Loyalty/rewards program — defer to v2

## Context

**Target Market:**
- Côte d'Ivoire (Abidjan initially), expanding to West Africa
- 100+ restaurants as initial target
- 10,000+ orders/day across all tenants
- Mobile money is dominant payment method (Wave especially popular)
- Unreliable internet requires offline-first architecture

**Technical Environment:**
- Django 5.0+ / Django REST Framework (backend)
- Next.js 14+ with TypeScript (POS PWA)
- React Native / Expo (mobile apps)
- PostgreSQL 15+ (Render managed)
- Redis (cache + Celery broker)
- Render.com (deployment platform)

**Development Approach:**
- Full TDD (tests before code)
- Monorepo structure
- 12-week build timeline
- French + English UI (i18n)

## Constraints

- **Platform:** Render.com for all hosting (web, worker, database, Redis)
- **Payments:** Direct API integration only (no payment aggregators)
- **Timeline:** 12 weeks to production-ready v1
- **Language:** French primary, English secondary
- **Offline:** POS must work without internet, sync when connected
- **Currency:** XOF (West African CFA franc) — no decimals

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Django over FastAPI | Team familiarity, DRF ecosystem, admin panel | — Pending |
| Shared DB multi-tenancy | Simpler ops than DB-per-tenant at 100 restaurants | — Pending |
| PWA over native POS | Single codebase, easier updates, sufficient for tablets | — Pending |
| Direct payment APIs | Avoid aggregator fees, full control over UX | — Pending |
| Twilio for WhatsApp (MVP) | Faster setup than Meta Business API | — Pending |
| Operation-based offline sync | Append-only orders avoid conflicts | — Pending |

---
*Last updated: 2026-02-03 after initialization*
