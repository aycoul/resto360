# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-03)

**Core value:** Restaurants can take orders, accept payments, and manage deliveries - even when internet is unreliable.
**Current focus:** Phase 4 - Payments (COMPLETE)

## Current Position

Phase: 4 of 9 (Payments)
Plan: 6 of 6 in current phase
Status: Phase complete
Last activity: 2026-02-04 - Completed 04-06-PLAN.md (Reconciliation and Refunds)

Progress: [███████████████████░░░░░░░░░░░░░░░░░] 53%

## Performance Metrics

**Velocity:**
- Total plans completed: 19
- Average duration: 9 minutes
- Total execution time: 3.1 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 3/3 | 33 min | 11 min |
| 02-pos-core | 7/7 | 75 min | 11 min |
| 03-inventory | 3/3 | 29 min | 10 min |
| 04-payments | 6/6 | 35 min | 6 min |

**Recent Trend:**
- Last 5 plans: 04-01 (9 min), 04-04 (8 min), 04-05 (6 min), 04-06 (12 min)
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
- [02-01]: TenantContextMixin for DRF tenant context (sets in initial(), clears in finalize_response())
- [02-01]: Dual managers: all_objects (unfiltered, first), objects (TenantManager, filtered)
- [02-01]: ViewSet querysets created in get_queryset(), not class-level
- [02-01]: XOF prices as integers (no decimals for CFA franc)
- [02-02]: WeasyPrint for PDF receipt generation (pure Python)
- [02-02]: Segno for QR codes (PNG/SVG/EPS support)
- [02-02]: Order item data copied at order time for historical accuracy
- [02-02]: DailySequence with SELECT FOR UPDATE for atomic order numbers
- [02-03]: JWT via query string for WebSocket auth (browsers can't set headers)
- [02-03]: InMemoryChannelLayer for testing (no Redis required in tests)
- [02-03]: Explicit signal functions for WebSocket broadcasting (not Django signals)
- [02-03]: Channel groups named kitchen_{restaurant_id} for multi-tenant isolation
- [02-05]: React Context for cart state - simpler than Zustand, no external dependency
- [02-05]: Offline-first order creation with pending ops queue
- [02-05]: POS component pattern: page -> layout(provider) -> grid -> cards
- [02-06]: Web Audio API beep for sound notifications - no external audio files
- [02-06]: 2-second delay before removing completed orders - visual confirmation
- [02-06]: Exponential backoff 1s-30s for WebSocket reconnection
- [02-07]: AllowAny permission for public menu endpoints
- [02-07]: Separate GuestOrderCreateSerializer for unauthenticated orders
- [02-07]: Bottom sheet modals for mobile-first cart and checkout
- [03-01]: F() expressions with select_for_update() for race-safe stock updates
- [03-01]: StockMovement records are immutable (save() raises error on updates)
- [03-01]: django-simple-history for StockItem audit trail
- [03-02]: Insufficient stock logs warning but does NOT block order completion
- [03-02]: Stock non-negative constraint respected - no negative movements
- [03-02]: Django post_save signal for order->inventory integration
- [03-02]: Guard pattern: check existing movements before processing
- [03-03]: Celery task as placeholder for production notifications (email/push/WebSocket)
- [03-03]: TenantContextMixin required for non-ModelViewSet to access restaurant context
- [03-03]: Model property over queryset annotation when property already exists
- [03-03]: 90-day max date range limit on movement reports
- [04-01]: FSMField with protected=True for payment status transitions
- [04-01]: Idempotency dual-path: cache first (fast), DB fallback (recovery)
- [04-01]: cache.add() for atomic SETNX locking in idempotency
- [04-02]: HMAC-SHA256 with timestamp for Wave webhook signature verification
- [04-02]: 5-minute max age for webhook replay attack protection
- [04-02]: Celery shared_task for async webhook processing
- [04-02]: Double-check locking pattern for concurrent webhook safety
- [04-02]: Wave expects amount as STRING, not integer
- [04-03]: OAuth token caching with 60s pre-expiry refresh
- [04-03]: Orange uses OUV currency code for XOF (API requirement)
- [04-03]: MTN sandbox uses EUR, production uses XOF
- [04-03]: Phone numbers stripped of + prefix for MTN partyId
- [04-03]: poll_payment_status: 30 retries at 2min intervals = 1 hour window
- [04-04]: CashProvider returns SUCCESS immediately (no PENDING->confirm flow)
- [04-04]: Use idempotency_key as provider_reference for cash payments
- [04-04]: One open drawer session per cashier enforced at API level
- [04-04]: ViewSet custom actions for workflow (open/current/close pattern)
- [04-05]: Idempotency enforced at service layer before DB insert
- [04-05]: Webhooks return 200 immediately, process async via Celery
- [04-05]: Polling scheduled for Orange/MTN due to unreliable webhooks
- [04-06]: Net amount = totals.amount - refunds.amount (can be negative)
- [04-06]: FSM transitions extended for PARTIALLY_REFUNDED -> PARTIALLY_REFUNDED and -> REFUNDED
- [04-06]: Router registration order: specific paths before empty path
- [04-06]: Use Model.all_objects.get(pk=pk) instead of refresh_from_db() for FSM fields

### Pending Todos

None yet.

### Blockers/Concerns

- GitHub repository secrets need to be configured for Render deploy hooks
- Render environment variables (ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS) need manual setup
- PWA placeholder icons need to be replaced with branded versions before production
- Docker not running during 02-02 execution - tests need verification when Docker available
- Redis required for production WebSocket (configured but needs running instance)
- WeasyPrint requires GTK libraries on Windows (missing, but not needed for tests)
- Celery worker needed for production low-stock alerts (task runs eagerly in tests)
- Orange Money API credentials needed for production (see 04-03-USER-SETUP.md)
- MTN MoMo API credentials needed for production (see 04-03-USER-SETUP.md)

## Session Continuity

Last session: 2026-02-04
Stopped at: Completed 04-06-PLAN.md (Reconciliation and Refunds)
Resume file: None

---
*Next step: Phase 4 complete - ready for Phase 5 (WhatsApp Notifications)*
