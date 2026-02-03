---
phase: 03-inventory
plan: 01
subsystem: inventory
tags: [django, inventory, stock-management, api, f-expressions]

dependency-graph:
  requires: [01-foundation, 02-pos-core]
  provides: [stock-items, stock-movements, inventory-api]
  affects: [03-02-recipe-mapping, 03-03-alerts]

tech-stack:
  added:
    - django-simple-history>=3.11.0
  patterns:
    - F() expressions for atomic updates
    - select_for_update() for row-level locking
    - Immutable audit records
    - TenantManager for multi-tenant filtering

key-files:
  created:
    - apps/api/apps/inventory/__init__.py
    - apps/api/apps/inventory/apps.py
    - apps/api/apps/inventory/models.py
    - apps/api/apps/inventory/services.py
    - apps/api/apps/inventory/serializers.py
    - apps/api/apps/inventory/views.py
    - apps/api/apps/inventory/urls.py
    - apps/api/apps/inventory/admin.py
    - apps/api/apps/inventory/migrations/0001_initial.py
    - apps/api/apps/inventory/tests/__init__.py
    - apps/api/apps/inventory/tests/factories.py
    - apps/api/apps/inventory/tests/conftest.py
    - apps/api/apps/inventory/tests/test_models.py
    - apps/api/apps/inventory/tests/test_api.py
  modified:
    - apps/api/config/settings/base.py
    - apps/api/config/urls.py
    - apps/api/requirements/base.txt

decisions:
  - id: inv-001
    decision: "Use F() expressions with select_for_update() for race-safe stock updates"
    rationale: "Prevents race conditions at database level, essential for concurrent operations"
  - id: inv-002
    decision: "StockMovement records are immutable - save() raises error on updates"
    rationale: "Audit trail integrity requires movements cannot be modified after creation"
  - id: inv-003
    decision: "Dual manager pattern: all_objects (unfiltered), objects (TenantManager)"
    rationale: "Consistent with existing models, allows both scoped and unscoped queries"

metrics:
  duration: 13 minutes
  completed: 2026-02-03
---

# Phase 3 Plan 1: Inventory Foundation Summary

**One-liner:** Atomic stock operations with F() expressions, immutable movement audit trail, and full CRUD API for inventory management.

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 81d53d0 | feat | Create inventory app with StockItem and StockMovement models |
| ba4ac7a | feat | Add atomic stock services with F() expressions |
| c6b8fb9 | feat | Add inventory API endpoints and comprehensive tests |

## What Was Built

### Models

1. **StockItem** - Track inventory items with:
   - name, sku (optional), unit (kg, g, L, mL, piece, portion, other)
   - current_quantity with non-negative constraint
   - low_stock_threshold and low_stock_alert_sent for alerts
   - is_active flag for soft delete
   - django-simple-history for audit trail
   - UniqueConstraint on (restaurant, sku) when sku is not empty

2. **StockMovement** - Immutable movement records:
   - stock_item FK with PROTECT on delete
   - quantity_change (positive for in, negative for out)
   - movement_type: in, out, adjustment
   - reason: purchase, order_usage, waste, theft, correction, transfer, initial
   - reference_type/reference_id for linking to orders
   - balance_after snapshot
   - created_by user tracking
   - Immutability enforced in save()

### Services

Atomic stock operations in `services.py`:

- **add_stock()** - Add stock with F() expression, clear low_stock_alert if above threshold
- **deduct_stock()** - Deduct with InsufficientStockError validation
- **adjust_stock()** - Set quantity to specific value (for corrections)
- **_check_low_stock_alert()** - Monitor threshold and set alert flags

All services use `transaction.atomic()` and `select_for_update()` for race safety.

### API Endpoints

```
GET    /api/v1/inventory/stock-items/          - List stock items
POST   /api/v1/inventory/stock-items/          - Create stock item
GET    /api/v1/inventory/stock-items/{id}/     - Retrieve stock item
PATCH  /api/v1/inventory/stock-items/{id}/     - Update stock item
DELETE /api/v1/inventory/stock-items/{id}/     - Delete stock item
POST   /api/v1/inventory/stock-items/{id}/add-stock/  - Add stock
POST   /api/v1/inventory/stock-items/{id}/adjust/     - Adjust stock
GET    /api/v1/inventory/stock-items/{id}/movements/  - Get movements

GET    /api/v1/inventory/movements/            - List all movements
GET    /api/v1/inventory/movements/{id}/       - Retrieve movement
```

### Tests

38 tests covering:
- Model creation and constraints
- Stock movement immutability
- is_low_stock property
- Unique SKU constraint per restaurant
- History tracking
- CRUD API operations
- add_stock and adjust actions
- Tenant isolation
- Permission checks (owner/manager vs cashier)

## Deviations from Plan

None - plan executed exactly as written.

## Technical Notes

1. **CheckConstraint Update**: Updated from `check=` to `condition=` parameter to fix Django 6.0 deprecation warning.

2. **TenantReadOnlyModelViewSet**: Created as base class for read-only viewsets with tenant context, since combining ReadOnlyModelViewSet with TenantContextMixin directly caused MRO issues.

3. **Factory Pattern**: StockMovementFactory uses LazyAttribute for created_by to avoid fixture dependency issues with pytest_factoryboy.

## Next Phase Readiness

Ready for Plan 03-02 (Recipe to Stock Item Mapping):
- StockItem model provides target for recipe ingredient mapping
- add_stock/deduct_stock services ready for recipe-based deductions
- Movement records will track order_usage reason for recipe deductions

## Verification Checklist

- [x] Models exist and migrations applied
- [x] StockItem has django-simple-history tracking
- [x] StockMovement is immutable (save raises ValueError)
- [x] Stock operations use F() expressions
- [x] API endpoints functional with proper permissions
- [x] Tenant isolation verified
- [x] All 38 tests pass
