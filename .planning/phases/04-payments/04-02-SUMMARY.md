---
phase: "04"
plan: "02"
subsystem: payments
tags: [wave, mobile-money, webhooks, celery, hmac, async]
depends_on:
  requires: ["04-01"]
  provides: ["Wave payment provider", "Webhook verification", "Async processing"]
  affects: ["04-05", "04-06"]
tech-stack:
  added: ["requests", "celery"]
  patterns: ["HMAC-SHA256 webhook verification", "Celery shared_task", "Double-check locking"]
key-files:
  created:
    - apps/api/apps/payments/providers/wave.py
    - apps/api/apps/payments/webhooks/__init__.py
    - apps/api/apps/payments/webhooks/verification.py
    - apps/api/apps/payments/webhooks/handlers.py
    - apps/api/apps/payments/tasks.py
    - apps/api/apps/payments/tests/test_wave.py
    - apps/api/apps/payments/tests/test_webhooks.py
  modified:
    - apps/api/config/settings/base.py
    - apps/api/apps/payments/providers/__init__.py
key-decisions:
  - "HMAC-SHA256 with timestamp for Wave webhook signature verification"
  - "5-minute max age for webhook replay attack protection"
  - "Celery shared_task for async webhook processing"
  - "Double-check locking pattern for concurrent webhook safety"
  - "Wave expects amount as STRING, not integer"
metrics:
  duration: "10 min"
  completed: "2026-02-04"
---

# Phase 4 Plan 2: Wave Money Provider Summary

Wave Money payment provider with webhook handling and async Celery processing for Ivory Coast's most popular mobile money service.

## Accomplishments

### Task 1: Implement Wave Provider (ae4b57b)
- Created `WaveProvider` class implementing `PaymentProvider` interface
- POST to `{api_url}/checkout/sessions` for payment initiation
- GET `{api_url}/checkout/sessions/{id}` for status checks
- POST refund endpoint support with partial/full refund
- Wave settings added to base.py: `WAVE_API_KEY`, `WAVE_WEBHOOK_SECRET`, `WAVE_API_URL`
- Added "wave" to `get_provider()` factory function
- **Key detail**: Wave expects amount as STRING, not integer

### Task 2: Webhook Verification and Async Processing (7472a6f)
- Created `webhooks/verification.py` with HMAC-SHA256 signature verification
- Signature format: `t={timestamp},v1={signature}`
- Signed payload: `{timestamp}.{body}`
- 5-minute max age for replay attack protection
- Created `webhooks/handlers.py` with idempotent Wave webhook handler
- Double-check locking pattern for concurrent webhook safety
- FSM transitions: PENDING -> PROCESSING -> SUCCESS/FAILED/EXPIRED
- Created `tasks.py` with Celery `@shared_task` for async processing
- Added `check_pending_payments` task for missed webhook recovery
- Added stub handlers for Orange/MTN (placeholders for future plans)

### Task 3: Wave Provider and Webhook Tests (31b7d85)
- 16 Wave provider tests covering:
  - Payment initiation (success, phone restriction, API error, network error)
  - Status checking (complete, pending, expired, network error)
  - Refund processing (full, partial, error)
  - Webhook parsing (completed, expired, invalid JSON)
- 7 signature verification tests covering:
  - Valid signature acceptance
  - Invalid signature rejection
  - Missing header, expired timestamp, case-insensitive header
  - Empty secret, malformed header
- 7 webhook handler tests covering:
  - Success/expired/failed status transitions
  - Idempotency (same event processed twice)
  - Payment not found, missing reference
  - PENDING -> SUCCESS transition path
- 3 Celery task tests covering:
  - Successful event processing
  - Invalid signature handling
  - Unknown provider error

**Total: 33 tests passing**

## Files Created/Modified

**Created:**
- `apps/api/apps/payments/providers/wave.py` - WaveProvider implementation
- `apps/api/apps/payments/webhooks/__init__.py` - Webhooks package init
- `apps/api/apps/payments/webhooks/verification.py` - HMAC-SHA256 signature verification
- `apps/api/apps/payments/webhooks/handlers.py` - Webhook event handlers
- `apps/api/apps/payments/tasks.py` - Celery tasks for async processing
- `apps/api/apps/payments/tests/test_wave.py` - Wave provider tests
- `apps/api/apps/payments/tests/test_webhooks.py` - Webhook tests

**Modified:**
- `apps/api/config/settings/base.py` - Added Wave settings
- `apps/api/apps/payments/providers/__init__.py` - Added wave to get_provider()

## Decisions Made

1. **HMAC-SHA256 with timestamp**: Wave webhook verification uses `t={timestamp},v1={signature}` header format with signed payload `{timestamp}.{body}`
2. **5-minute replay protection**: Webhooks older than 300 seconds are rejected to prevent replay attacks
3. **Celery shared_task**: Using `@shared_task` (not `@app.task`) for portability across Celery configurations
4. **Double-check locking**: Fetch payment, check state, lock (select_for_update), check again, update
5. **Amount as string**: Wave API expects amount as string ("10000"), not integer (10000)
6. **Stub handlers added**: Orange and MTN handlers added as placeholders returning None (will be implemented in 04-03, 04-04)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed requests library**
- **Found during:** Task 1 verification
- **Issue:** `requests` module not installed in virtualenv
- **Fix:** `pip install requests` to enable HTTP calls to Wave API
- **Impact:** None - standard dependency for HTTP requests

**2. [Rule 3 - Blocking] Installed Celery**
- **Found during:** Task 2 verification
- **Issue:** `celery` module not installed in virtualenv
- **Fix:** `pip install celery` to enable async task processing
- **Impact:** None - required for webhook async processing

**3. [Rule 2 - Missing Critical] Added stub handlers for Orange/MTN**
- **Found during:** Task 3 test execution
- **Issue:** tasks.py imports `handle_orange_webhook` and `handle_mtn_webhook` that didn't exist
- **Fix:** Added stub handlers that return None with TODO comments
- **Impact:** Tests pass, handlers ready for implementation in 04-03, 04-04

## Verification Results

```
apps/payments/tests/test_wave.py - 16 passed
apps/payments/tests/test_webhooks.py - 17 passed
Total: 33 passed, 0 failed
```

All success criteria met:
- [x] WaveProvider creates checkout sessions via Wave API
- [x] Webhook signatures verified using HMAC-SHA256 with timestamp
- [x] Webhook events processed asynchronously via Celery
- [x] Payment status updated (SUCCESS, EXPIRED, FAILED) based on webhook
- [x] 33 tests pass covering provider, verification, and handlers (exceeds 12+ requirement)

## Next Phase Readiness

**Ready for:** 04-03-PLAN.md (Orange Money and MTN MoMo providers)

**Blockers:** None

**Notes:**
- Wave provider requires `WAVE_API_KEY` and `WAVE_WEBHOOK_SECRET` environment variables for production
- Celery worker must be running for async webhook processing in production
- Stub handlers for Orange/MTN are in place, ready for implementation

---
*Completed: 2026-02-04 04:08 UTC*
*Duration: 10 minutes*
*Commits: ae4b57b, 7472a6f, 31b7d85*
