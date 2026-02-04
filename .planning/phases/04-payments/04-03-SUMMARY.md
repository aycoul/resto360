---
phase: 04-payments
plan: 03
subsystem: payments
tags: [orange-money, mtn-momo, mobile-money, celery, polling, oauth, west-africa]

# Dependency graph
requires:
  - phase: 04-01
    provides: PaymentProvider ABC, Payment model with FSM, idempotency service
provides:
  - OrangeProvider with OAuth token caching
  - MTNProvider with environment-aware configuration
  - poll_payment_status Celery task for unreliable webhooks
  - Orange and MTN webhook handlers
  - 25 provider tests
affects: [04-05-api-views, 04-06-reconciliation, payment-processing]

# Tech tracking
tech-stack:
  added: []  # requests already installed
  patterns:
    - OAuth token caching with expiry tracking
    - Environment-aware provider configuration (sandbox vs production)
    - Polling fallback for unreliable webhooks

key-files:
  created:
    - apps/api/apps/payments/providers/orange.py
    - apps/api/apps/payments/providers/mtn.py
    - apps/api/apps/payments/tests/test_orange.py
    - apps/api/apps/payments/tests/test_mtn.py
  modified:
    - apps/api/apps/payments/providers/__init__.py
    - apps/api/apps/payments/webhooks/handlers.py
    - apps/api/apps/payments/tasks.py
    - apps/api/config/settings/base.py

key-decisions:
  - "Orange uses OUV currency code for XOF (API requirement)"
  - "MTN sandbox uses EUR, production uses XOF (API limitation)"
  - "Phone numbers stripped of + prefix for MTN (partyId requirement)"
  - "202 Accepted from MTN means request received, not success"
  - "Polling essential: Orange webhooks unreliable, MTN sandbox has no callbacks"
  - "30 retries at 2-minute intervals = 1 hour total polling window"

patterns-established:
  - "OAuth token caching: cache token with expiry timestamp, refresh 60s before expiry"
  - "Environment detection: use settings.MTN_ENVIRONMENT to determine base URL and currency"
  - "Provider-specific currency mapping: convert XOF to OUV for Orange"

# Metrics
duration: 27 min
completed: 2026-02-04
---

# Phase 04 Plan 03: Orange Money and MTN MoMo Providers Summary

**Orange Money and MTN MoMo payment providers with OAuth token caching, environment-aware configuration, and poll_payment_status task for webhook fallback**

## Performance

- **Duration:** 27 min
- **Started:** 2026-02-04T03:59:56Z
- **Completed:** 2026-02-04T04:27:22Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- OrangeProvider implementing full PaymentProvider interface with OAuth token caching
- MTNProvider with sandbox/production environment detection and currency handling
- poll_payment_status Celery task polling PROCESSING payments up to 30 times (1 hour)
- Orange and MTN webhook handlers integrated into process_webhook_event routing
- 25 comprehensive tests covering both providers (10 Orange, 15 MTN)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement Orange Money provider** - `6c1feef` (feat)
2. **Task 2: Implement MTN MoMo provider** - `34cc433` (feat)
3. **Task 3: Add polling task and tests** - `6658e9e` (feat)

## Files Created/Modified

- `apps/api/apps/payments/providers/orange.py` - OrangeProvider with OAuth, OUV currency, pay_token handling
- `apps/api/apps/payments/providers/mtn.py` - MTNProvider with environment detection, X-Reference-Id tracking
- `apps/api/apps/payments/providers/__init__.py` - Added orange and mtn to get_provider mapping
- `apps/api/apps/payments/webhooks/handlers.py` - Added handle_orange_webhook, handle_mtn_webhook
- `apps/api/apps/payments/tasks.py` - Added poll_payment_status task, routing for Orange/MTN
- `apps/api/config/settings/base.py` - Added Orange and MTN configuration settings
- `apps/api/apps/payments/tests/test_orange.py` - 10 tests for OrangeProvider
- `apps/api/apps/payments/tests/test_mtn.py` - 15 tests for MTNProvider

## Decisions Made

1. **OAuth token caching** - Cache token with expiry timestamp, refresh 60s before expiry to avoid failed requests
2. **OUV for Orange** - Orange API requires "OUV" currency code instead of "XOF"
3. **EUR for MTN sandbox** - MTN sandbox only accepts EUR; production uses XOF for Ivory Coast
4. **Phone number formatting** - Strip + prefix for MTN partyId field (required by API)
5. **Polling over webhooks** - Orange webhooks unreliable, MTN sandbox has no callbacks - polling essential
6. **30 retry limit** - 30 retries at 2-minute intervals gives 1-hour window for customer approval

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed requests package**
- **Found during:** Task 1 (Orange provider import)
- **Issue:** requests module not installed in venv
- **Fix:** Ran `pip install requests`
- **Files modified:** (venv, not committed)
- **Verification:** Import succeeded, tests passed
- **Committed in:** Part of development environment

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential for HTTP client functionality. No scope creep.

## Issues Encountered

- Parallel execution conflict with 04-02 (Wave provider) - coordinated by working with modified files
- Linter reverted Orange/MTN handler imports - re-applied changes

## User Setup Required

**External services require manual configuration.** See [04-03-USER-SETUP.md](./04-03-USER-SETUP.md) for:
- Orange Money: ORANGE_CLIENT_ID, ORANGE_CLIENT_SECRET, ORANGE_MERCHANT_KEY
- MTN MoMo: MTN_SUBSCRIPTION_KEY, MTN_USER_ID, MTN_API_SECRET

## Next Phase Readiness

- All 4 payment providers ready: Cash, Wave, Orange, MTN
- Webhook handlers complete for all providers
- Polling task ready for unreliable webhook scenarios
- Ready for 04-05 (Payment API views) to expose endpoints
- Ready for 04-06 (Reconciliation) to use provider status checks

---
*Phase: 04-payments*
*Completed: 2026-02-04*
