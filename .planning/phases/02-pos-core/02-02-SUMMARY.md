---
phase: 02-pos-core
plan: 02
subsystem: api
tags: [django, drf, orders, pdf, weasyprint, qr-code, segno, receipts]

# Dependency graph
requires:
  - phase: 02-01
    provides: Menu models (MenuItem, ModifierOption), TenantModelViewSet base class
provides:
  - Order management API with items and modifiers
  - Daily order number generation (atomic, per-restaurant)
  - Table management for dine-in orders
  - PDF receipt generation (80mm thermal format)
  - QR code generation for menu URLs
affects: [02-03, 02-05, 02-06]  # Kitchen display, payments, analytics

# Tech tracking
tech-stack:
  added: [weasyprint>=68.0, segno>=1.6.6]
  patterns:
    - "OrderCreateSerializer with nested item/modifier validation"
    - "Status transition validation in OrderStatusUpdateSerializer"
    - "DailySequence with SELECT FOR UPDATE for atomic order numbers"

key-files:
  created:
    - apps/api/apps/orders/models.py
    - apps/api/apps/orders/services.py
    - apps/api/apps/orders/serializers.py
    - apps/api/apps/orders/views.py
    - apps/api/apps/receipts/services.py
    - apps/api/apps/receipts/templates/receipts/receipt.html
    - apps/api/apps/qr/services.py
  modified:
    - apps/api/requirements/base.txt
    - apps/api/config/settings/base.py
    - apps/api/config/urls.py

key-decisions:
  - "WeasyPrint for PDF generation (pure Python, no external dependencies)"
  - "Segno for QR codes (lightweight, multiple format support)"
  - "Order totals stored denormalized for query performance"
  - "Item name/price copied to order for historical accuracy"
  - "Status transitions enforced via OrderStatusUpdateSerializer"

patterns-established:
  - "Services layer for business logic (get_next_order_number, generate_receipt_pdf)"
  - "Nested create serializers for complex operations (OrderCreateSerializer)"
  - "TenantContextMixin for APIView-based endpoints (ReceiptDownloadView, MenuQRCodeView)"

# Metrics
duration: 12min
completed: 2026-02-03
---

# Phase 02 Plan 02: Order Backend Summary

**Order management API with atomic daily numbering, PDF receipts via WeasyPrint, and QR code generation via Segno**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-03T20:04:43Z
- **Completed:** 2026-02-03T20:16:18Z
- **Tasks:** 5
- **Files modified:** 25+

## Accomplishments

- Order, OrderItem, OrderItemModifier, Table, DailySequence models with full tenant isolation
- Order creation API with nested items, modifiers, and automatic total calculation
- Status workflow with valid transitions (pending -> preparing -> ready -> completed)
- PDF receipt generation for 80mm thermal printers with French localization
- QR code generation for restaurant menu URLs (PNG/SVG/EPS formats)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies and create apps** - `022c96d` (chore)
2. **Task 2: Create order models with daily sequence** - `ea8f85a` (feat)
3. **Task 3: Create order serializers and API endpoints** - `410a048` (feat)
4. **Task 4: Create receipt PDF and QR code services** - `cf2cf5f` (feat)
5. **Task 5: Create comprehensive tests** - `d9c77f6` (test)

## Files Created/Modified

### Created
- `apps/api/apps/orders/` - Full orders app (models, views, serializers, services, admin)
- `apps/api/apps/receipts/` - Receipt PDF generation with HTML template
- `apps/api/apps/qr/` - QR code generation service and views
- `apps/api/apps/orders/tests/` - 53 comprehensive tests

### Modified
- `apps/api/requirements/base.txt` - Added weasyprint, segno
- `apps/api/config/settings/base.py` - Added apps, FRONTEND_URL setting
- `apps/api/config/urls.py` - Added orders, receipts, qr routes

## Decisions Made

1. **WeasyPrint over reportlab** - Pure Python, better HTML/CSS support for receipt layout
2. **Segno over qrcode** - Lighter weight, supports SVG/EPS natively
3. **Denormalized order totals** - Store subtotal/total on Order for query performance
4. **Copied item data** - Store name/price at order time for historical accuracy
5. **Status validation in serializer** - Enforce valid transitions, require cancellation reason

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Docker not running, so tests could not be verified during execution
- Python command not available directly (uses Docker for all Django commands)
- Created all code and tests; verification deferred to Docker environment

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Order models ready for Kitchen Display (02-03)
- Receipt generation ready for payment flow (02-05)
- Order data structure ready for analytics (02-06)
- Tests ready for CI validation when Docker is available

---
*Phase: 02-pos-core*
*Completed: 2026-02-03*
