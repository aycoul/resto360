---
phase: 03-inventory
plan: 02
subsystem: inventory
tags: [django-signals, recipe-mapping, stock-deduction, order-integration]

# Dependency graph
requires:
  - phase: 03-01
    provides: StockItem model, StockMovement model, atomic stock services, TenantModel pattern
  - phase: 02-02
    provides: Order model, OrderItem model, OrderStatus enum
  - phase: 02-01
    provides: Menu model, MenuItem model
provides:
  - MenuItemIngredient model for recipe/BOM mapping
  - deduct_ingredients_for_order service function
  - Order completion signal handler for automatic stock deduction
  - Recipe CRUD API at /api/inventory/recipes/
affects: [03-03, reporting, analytics, inventory-alerts]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Django post_save signal for cross-app integration"
    - "Service function for order ingredient deduction"
    - "Lazy import in signals to avoid circular dependencies"
    - "Guard against duplicate signal processing via movement check"

key-files:
  created:
    - apps/api/apps/inventory/signals.py
    - apps/api/apps/inventory/tests/test_services.py
    - apps/api/apps/inventory/tests/test_signals.py
  modified:
    - apps/api/apps/inventory/models.py
    - apps/api/apps/inventory/services.py
    - apps/api/apps/inventory/serializers.py
    - apps/api/apps/inventory/views.py
    - apps/api/apps/inventory/urls.py
    - apps/api/apps/inventory/admin.py
    - apps/api/apps/inventory/apps.py
    - apps/api/apps/inventory/tests/factories.py
    - apps/api/apps/inventory/tests/conftest.py

key-decisions:
  - "Insufficient stock logs warning but does NOT block order completion"
  - "Stock non-negative constraint respected - no negative movements created"
  - "Signal guards against duplicate processing via StockMovement reference check"
  - "Deduction only on completed status (not pending/preparing/ready/cancelled)"

patterns-established:
  - "Signal registration in AppConfig.ready() for cross-app integration"
  - "Lazy imports in signals to avoid circular dependency issues"
  - "Guard pattern: check existing movements before processing"
  - "Recipe mapping pattern: MenuItemIngredient links MenuItem to StockItem"

# Metrics
duration: 9min
completed: 2026-02-04
---

# Phase 3 Plan 2: Recipe Mapping and Order Stock Deduction Summary

**MenuItemIngredient model for recipe mapping with automatic stock deduction on order completion via Django signals**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-03T22:04:27Z
- **Completed:** 2026-02-03T22:13:29Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- MenuItemIngredient model linking MenuItem to StockItem with quantity_required per unit
- Automatic stock deduction triggered by Order.status = 'completed' via Django signal
- Recipe CRUD API at /api/inventory/recipes/ with menu_item/stock_item filtering
- 19 new tests for service functions and signal integration
- All 57 inventory tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create MenuItemIngredient model** - `07b622e` (feat)
2. **Task 2: Create order completion signal and deduction service** - `c59b9c7` (feat)
3. **Task 3: Create recipe API endpoints and tests** - `d85472d` (feat)

## Files Created/Modified

- `apps/api/apps/inventory/models.py` - Added MenuItemIngredient model
- `apps/api/apps/inventory/signals.py` - Order completion signal handler (new)
- `apps/api/apps/inventory/services.py` - Added deduct_ingredients_for_order function
- `apps/api/apps/inventory/serializers.py` - Added MenuItemIngredientSerializer
- `apps/api/apps/inventory/views.py` - Added MenuItemIngredientViewSet
- `apps/api/apps/inventory/urls.py` - Registered recipes endpoint
- `apps/api/apps/inventory/admin.py` - Added MenuItemIngredientAdmin
- `apps/api/apps/inventory/apps.py` - Signal registration in ready()
- `apps/api/apps/inventory/migrations/0002_menuitemingredient.py` - Migration
- `apps/api/apps/inventory/tests/factories.py` - Added MenuItemIngredientFactory
- `apps/api/apps/inventory/tests/conftest.py` - Added order_with_ingredients fixtures
- `apps/api/apps/inventory/tests/test_services.py` - Service tests (new)
- `apps/api/apps/inventory/tests/test_signals.py` - Signal tests (new)

## Decisions Made

1. **Insufficient stock handling:** The plan specified creating negative movements for tracking discrepancies, but 03-01 established a CHECK constraint preventing negative stock. Decision: Respect the constraint, log warning only. Manual inventory adjustments can correct discrepancies.

2. **Signal guard pattern:** Used StockMovement reference check to prevent duplicate processing on order re-saves, rather than tracking in a separate field.

3. **Lazy imports in signals:** Used late imports inside signal handlers to avoid circular dependency issues between inventory and orders apps.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed insufficient stock handling to respect non-negative constraint**

- **Found during:** Task 3 (tests)
- **Issue:** Plan called for _create_negative_balance_movement but model has CHECK constraint preventing negative stock
- **Fix:** Removed negative movement creation, kept warning log as audit trail
- **Files modified:** apps/api/apps/inventory/services.py
- **Verification:** Tests pass, constraint respected
- **Committed in:** d85472d (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug - plan/implementation conflict)
**Impact on plan:** Essential fix to respect data integrity constraints from 03-01. Warning logs provide audit trail for insufficient stock situations.

## Issues Encountered

None - execution proceeded smoothly after fixing the constraint conflict.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Recipe mapping complete, managers can associate ingredients with menu items
- Stock deduction automatic on order completion
- Ready for Phase 03-03: Low Stock Alerts and Notifications

**API Endpoints Available:**
- `GET /api/inventory/recipes/` - List all recipe mappings
- `POST /api/inventory/recipes/` - Create mapping
- `GET /api/inventory/recipes/?menu_item={id}` - Filter by menu item
- `GET /api/inventory/recipes/?stock_item={id}` - Filter by stock item
- `GET/PUT/PATCH/DELETE /api/inventory/recipes/{id}/` - Detail operations

---
*Phase: 03-inventory*
*Completed: 2026-02-04*
