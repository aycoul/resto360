---
phase: 03-inventory
plan: 03
subsystem: api
tags: [celery, async-tasks, reports, inventory, low-stock-alerts, drf]

# Dependency graph
requires:
  - phase: 03-01
    provides: StockItem model, services, movement records
  - phase: 03-02
    provides: Recipe mappings, order completion signal
provides:
  - Low stock alert Celery task with async notification
  - Current stock report endpoint with is_low_stock annotation
  - Low stock report endpoint filtering below-threshold items
  - Movement report endpoint with date range and breakdown
affects: [04-payments, dashboard, notifications]

# Tech tracking
tech-stack:
  added: [celery>=5.4]
  patterns: [Celery shared_task with retries, TenantContextMixin for ViewSet]

key-files:
  created:
    - apps/api/apps/inventory/tasks.py
    - apps/api/apps/inventory/tests/test_reports.py
  modified:
    - apps/api/apps/inventory/services.py
    - apps/api/apps/inventory/views.py
    - apps/api/apps/inventory/serializers.py
    - apps/api/apps/inventory/urls.py
    - apps/api/requirements/base.txt

key-decisions:
  - "Celery task logs alert (placeholder for email/push/WebSocket in production)"
  - "Model is_low_stock property used instead of queryset annotation"
  - "TenantContextMixin required for non-ModelViewSet to access restaurant"
  - "90-day max date range limit on movement reports"

patterns-established:
  - "TenantContextMixin: Use for any ViewSet needing restaurant context"
  - "Celery shared_task: bind=True, max_retries=3, default_retry_delay=60"
  - "Report serializers: Request validation separate from response serialization"

# Metrics
duration: 7min
completed: 2026-02-04
---

# Phase 3 Plan 3: Low Stock Alerts and Reports Summary

**Celery-based low stock alert system with async notifications plus REST report endpoints for current stock, low stock items, and movement history with date range filtering**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-03T22:16:17Z
- **Completed:** 2026-02-03T22:23:30Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Created Celery task `send_low_stock_alert` with retry logic for async notifications
- Implemented `_check_low_stock_alert` to trigger Celery task on threshold crossing
- Added report services: `get_current_stock_report`, `get_movement_report`, `get_stock_item_movement_history`
- Created ReportViewSet with three endpoints: current-stock, low-stock, movements
- Added comprehensive test coverage (15 new tests for reports, 72 total inventory tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement low stock alert system** - `d246b7a` (feat)
2. **Task 2: Create inventory report services** - `f3fd349` (feat)
3. **Task 3: Create report API endpoints and tests** - `ebdaa7a` (feat)

## Files Created/Modified

- `apps/api/apps/inventory/tasks.py` - Celery task for low stock notifications
- `apps/api/apps/inventory/services.py` - Report generation functions and updated alert logic
- `apps/api/apps/inventory/views.py` - ReportViewSet with current-stock, low-stock, movements endpoints
- `apps/api/apps/inventory/serializers.py` - Report request/response serializers
- `apps/api/apps/inventory/urls.py` - Added reports router registration
- `apps/api/apps/inventory/tests/test_reports.py` - 15 tests for report endpoints
- `apps/api/requirements/base.txt` - Added celery>=5.4

## Decisions Made

1. **Celery task as placeholder:** Task logs alerts instead of sending actual notifications. Production implementation will add email, WebSocket broadcast, and SMS integration.

2. **Model property over annotation:** Used existing `StockItem.is_low_stock` property instead of queryset annotation to avoid conflict with read-only property setter.

3. **TenantContextMixin for ViewSet:** ReportViewSet needs TenantContextMixin (not just TenantModelViewSet) because it's a plain ViewSet that calls `get_current_restaurant()`.

4. **90-day date range limit:** Movement report enforces max 90-day range to prevent expensive queries on large datasets.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added Celery dependency**
- **Found during:** Task 1 (Celery task creation)
- **Issue:** Celery package was not in requirements, import failed
- **Fix:** Added `celery>=5.4,<6.0` to requirements/base.txt and installed
- **Files modified:** apps/api/requirements/base.txt
- **Verification:** Import succeeds, task registered
- **Committed in:** d246b7a (Task 1 commit)

**2. [Rule 1 - Bug] Fixed is_low_stock annotation conflict**
- **Found during:** Task 3 (Report endpoint testing)
- **Issue:** Queryset annotation named `is_low_stock` conflicted with model's read-only property
- **Fix:** Removed annotation, rely on model's `is_low_stock` property instead
- **Files modified:** apps/api/apps/inventory/services.py
- **Verification:** Tests pass, serializer correctly reads property value
- **Committed in:** ebdaa7a (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correct operation. No scope creep.

## Issues Encountered

- None beyond the auto-fixed deviations documented above.

## User Setup Required

None - no external service configuration required. Celery task will run when Celery worker is available (uses `CELERY_TASK_ALWAYS_EAGER=True` in test settings).

## Next Phase Readiness

- Phase 3 (Inventory Management) is now complete
- Low stock alerts ready for production notification integration
- Report endpoints ready for dashboard consumption
- All 72 inventory tests pass

---
*Phase: 03-inventory*
*Completed: 2026-02-04*
