# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-03)

**Core value:** Restaurants can take orders, accept payments, and manage deliveries - even when internet is unreliable.
**Current focus:** Phase 2 - POS Core

## Current Position

Phase: 2 of 9 (POS Core)
Plan: 4 of 7 in current phase
Status: In progress
Last activity: 2026-02-03 - Completed 02-04-PLAN.md (Next.js PWA Foundation)

Progress: [████......] 41%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 12 minutes
- Total execution time: 0.80 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 3/3 | 33 min | 11 min |
| 02-pos-core | 1/7 | 15 min | 15 min |

**Recent Trend:**
- Last 5 plans: 01-01 (11 min), 01-02 (18 min), 01-03 (3 min), 02-04 (15 min)
- Trend: Efficient execution

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Pre-build]: Tech stack - Django 5.0+/DRF backend, Next.js 14+ PWA, React Native/Expo mobile, PostgreSQL, Redis, Render.com
- [Pre-build]: WhatsApp provider - Start with Twilio, migrate to Meta Business API at scale
- [Pre-build]: Offline strategy - IndexedDB with operation-based sync, server authority for conflicts
- [01-01]: Django 5.2.11 LTS selected for stability
- [01-01]: Argon2 as primary password hasher
- [01-01]: Settings hierarchy (base/dev/prod/test) pattern
- [01-01]: SimpleJWT with 15min access, 7day refresh, rotation enabled
- [01-02]: Phone as username (Ivory Coast market standard)
- [01-02]: UUID primary keys on all models
- [01-02]: contextvars for thread-safe tenant context
- [01-02]: Role hierarchy: owner > manager > cashier > kitchen/driver
- [01-03]: PostgreSQL 15 and Redis 7 for local dev consistency with production
- [01-03]: Frankfurt region for Render (closest to West Africa)
- [01-03]: Separate lint, test, security jobs for parallel CI execution
- [02-04]: Next.js 16.1.6 with Turbopack selected
- [02-04]: @ducanh2912/next-pwa for PWA support
- [02-04]: next-intl v4 for i18n with French as default locale
- [02-04]: Dexie 4.x for IndexedDB offline storage

### Pending Todos

None yet.

### Blockers/Concerns

- GitHub repository secrets need to be configured for Render deploy hooks
- Render environment variables (ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS) need manual setup
- PWA placeholder icons need to be replaced with branded versions before production

## Session Continuity

Last session: 2026-02-03
Stopped at: Completed 02-04-PLAN.md
Resume file: None

---
*Next step: Execute 02-05 (POS cashier interface) or 02-01/02-02/02-03 (backend)*
