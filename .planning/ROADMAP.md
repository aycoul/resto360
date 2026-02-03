# Roadmap: RESTO360

## Overview

RESTO360 is an enterprise restaurant operating system for West Africa, delivering POS, mobile money payments, delivery management, WhatsApp ordering, supplier marketplace, and embedded financing. This roadmap transforms 81 requirements across 9 categories into a 12-week build delivering a complete restaurant management platform that works even when internet is unreliable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Foundation** - Multi-tenant infrastructure, auth, roles, CI/CD ✓
- [ ] **Phase 2: POS Core** - Menu management, order creation, offline-first PWA
- [ ] **Phase 3: Inventory** - Stock tracking, alerts, automatic deduction
- [ ] **Phase 4: Payments** - Wave, Orange, MTN mobile money integration
- [ ] **Phase 5: Delivery** - Zones, drivers, GPS tracking, mobile apps
- [ ] **Phase 6: WhatsApp** - Order via chat, NLP parsing, notifications
- [ ] **Phase 7: Suppliers** - Catalog, purchase orders, reorder suggestions
- [ ] **Phase 8: Finance** - Credit scoring, loans, cash advances
- [ ] **Phase 9: Analytics** - Sales reports, trends, performance metrics

## Phase Details

### Phase 1: Foundation
**Goal**: Restaurant owners and staff can securely access the platform with appropriate permissions
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06
**Success Criteria** (what must be TRUE):
  1. Restaurant owner can create account and configure restaurant settings (name, address, timezone, XOF currency)
  2. Owner can invite staff members with specific roles (manager, cashier, kitchen, driver)
  3. Staff can log in and see only features their role permits
  4. Code changes trigger automated tests and deploy to staging
  5. Developer can spin up complete local environment with single command
**Plans**: 3 plans in 2 waves

Plans:
- [x] 01-01-PLAN.md - Project scaffolding and monorepo setup (Wave 1) ✓
- [x] 01-02-PLAN.md - Multi-tenant database and authentication (Wave 2) ✓
- [x] 01-03-PLAN.md - CI/CD pipeline and development environment (Wave 2) ✓

### Phase 2: POS Core
**Goal**: Cashiers can take orders and kitchen can prepare them, even when internet is down
**Depends on**: Phase 1
**Requirements**: POS-01, POS-02, POS-03, POS-04, POS-05, POS-06, POS-07, POS-08, POS-09, POS-10, POS-11, POS-12, POS-13, POS-14, POS-15
**Success Criteria** (what must be TRUE):
  1. Manager can create menu categories and items with prices, images, and modifiers
  2. Cashier can build cart, select order type (dine-in/takeout/delivery), and submit order
  3. Kitchen display shows order queue with status updates (pending -> preparing -> ready)
  4. Orders created offline sync automatically when connection restored
  5. Customers can scan QR code, view menu, and place order from their phone
**Plans**: 7 plans in 4 waves

Plans:
- [ ] 02-01-PLAN.md - Menu management backend (Category, MenuItem, Modifier models + API) (Wave 1)
- [ ] 02-02-PLAN.md - Order management backend (Order, OrderItem, DailySequence + Receipt PDF + QR) (Wave 2)
- [ ] 02-03-PLAN.md - Kitchen WebSocket (Django Channels real-time order updates) (Wave 3)
- [ ] 02-04-PLAN.md - Next.js PWA foundation (i18n, Dexie IndexedDB, API client) (Wave 1)
- [ ] 02-05-PLAN.md - POS cashier interface (Menu grid, cart, offline-first orders) (Wave 3)
- [ ] 02-06-PLAN.md - Kitchen display frontend (Real-time order queue with WebSocket) (Wave 4)
- [ ] 02-07-PLAN.md - Customer QR menu (Public menu page, self-ordering) (Wave 4)

### Phase 3: Inventory
**Goal**: Restaurant knows stock levels in real-time and never runs out of key ingredients unexpectedly
**Depends on**: Phase 2
**Requirements**: INV-01, INV-02, INV-03, INV-04, INV-05, INV-06
**Success Criteria** (what must be TRUE):
  1. Manager can add stock items with SKU, quantity, and unit of measure
  2. System tracks all stock movements (receipts, usage, adjustments) with audit trail
  3. Low stock alerts appear when items fall below configured threshold
  4. Completing an order automatically deducts ingredients based on menu item recipes
  5. Manager can view current stock levels and movement history reports
**Plans**: TBD

Plans:
- [ ] 03-01: Stock item management and movement tracking
- [ ] 03-02: Menu-to-ingredient mapping and auto-deduction
- [ ] 03-03: Low stock alerts and inventory reports

### Phase 4: Payments
**Goal**: Restaurant can accept all major mobile money providers and reconcile daily
**Depends on**: Phase 2
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, PAY-05, PAY-06, PAY-07, PAY-08, PAY-09, PAY-10, PAY-11
**Success Criteria** (what must be TRUE):
  1. Customer can pay via Wave Money and transaction completes within 30 seconds
  2. Customer can pay via Orange Money and transaction completes within 30 seconds
  3. Customer can pay via MTN MoMo and transaction completes within 30 seconds
  4. Cashier can record cash payments with drawer tracking
  5. Manager can view daily reconciliation report showing all payments by method
**Plans**: TBD

Plans:
- [ ] 04-01: Payment model and provider abstraction
- [ ] 04-02: Wave Money integration
- [ ] 04-03: Orange Money and MTN MoMo integration
- [ ] 04-04: Cash payments, receipts, and reconciliation

### Phase 5: Delivery
**Goal**: Restaurant can manage delivery orders end-to-end with real-time tracking
**Depends on**: Phase 2, Phase 4
**Requirements**: DEL-01, DEL-02, DEL-03, DEL-04, DEL-05, DEL-06, DEL-07, DEL-08, DEL-09, DEL-10, DEL-11, DEL-12, DEL-13, DEL-14, DEL-15
**Success Criteria** (what must be TRUE):
  1. Manager can configure delivery zones with polygon boundaries, fees, and minimum order
  2. Driver can go online/offline, see assigned deliveries, and navigate to addresses
  3. System automatically assigns nearest available driver to new delivery orders
  4. Customer can track delivery in real-time on map and contact driver
  5. Delivery is confirmed with customer signature or photo proof
**Plans**: TBD

Plans:
- [ ] 05-01: Delivery zones and driver management
- [ ] 05-02: Assignment algorithm and status tracking
- [ ] 05-03: Driver mobile app (React Native)
- [ ] 05-04: Customer mobile app with real-time tracking

### Phase 6: WhatsApp
**Goal**: Customers can order via WhatsApp conversation and receive status updates
**Depends on**: Phase 2, Phase 4, Phase 5
**Requirements**: WA-01, WA-02, WA-03, WA-04, WA-05, WA-06, WA-07, WA-08, WA-09, WA-10
**Success Criteria** (what must be TRUE):
  1. Customer can message restaurant on WhatsApp and see the menu
  2. Customer can place order through natural conversation (AI parses intent)
  3. Customer receives payment link and can complete payment
  4. Customer receives order status notifications (preparing, out for delivery, delivered)
  5. Restaurant can view conversation history per customer
**Plans**: TBD

Plans:
- [ ] 06-01: WhatsApp Business API integration (Twilio)
- [ ] 06-02: Message parser and conversation state machine
- [ ] 06-03: Order building and payment link flow
- [ ] 06-04: Status notifications and conversation history

### Phase 7: Suppliers
**Goal**: Restaurant can order supplies from verified suppliers and track deliveries
**Depends on**: Phase 3
**Requirements**: SUP-01, SUP-02, SUP-03, SUP-04, SUP-05, SUP-06, SUP-07, SUP-08
**Success Criteria** (what must be TRUE):
  1. Supplier can register and list products with prices and lead times
  2. Restaurant can browse supplier catalogs and create purchase orders
  3. Restaurant tracks purchase order status from pending to delivered
  4. System suggests reorders based on low stock alerts
  5. Restaurant can manage supplier invoices and view purchase history
**Plans**: TBD

Plans:
- [ ] 07-01: Supplier registration and product catalog
- [ ] 07-02: Purchase order creation and tracking
- [ ] 07-03: Auto-reorder suggestions and invoice management

### Phase 8: Finance
**Goal**: Restaurants can access working capital through loans and cash advances based on sales history
**Depends on**: Phase 4
**Requirements**: FIN-01, FIN-02, FIN-03, FIN-04, FIN-05, FIN-06, FIN-07, FIN-08, FIN-09, FIN-10
**Success Criteria** (what must be TRUE):
  1. System aggregates daily/weekly/monthly sales data for credit scoring
  2. Restaurant can apply for business loan and see terms (amount, interest, monthly payment)
  3. Approved loans are disbursed via mobile money
  4. Repayments are tracked with clear schedule and status
  5. Restaurant can apply for cash advance with repayment via percentage of daily sales
**Plans**: TBD

Plans:
- [ ] 08-01: Sales aggregation and credit scoring
- [ ] 08-02: Loan application and approval workflow
- [ ] 08-03: Disbursement, repayment tracking, and cash advances

### Phase 9: Analytics
**Goal**: Restaurant owners have visibility into business performance and trends
**Depends on**: Phase 2, Phase 4, Phase 5
**Requirements**: ANA-01, ANA-02, ANA-03, ANA-04, ANA-05, ANA-06
**Success Criteria** (what must be TRUE):
  1. Owner can view daily sales summary (revenue, order count, average order value)
  2. Owner can see item popularity report (top sellers, slow movers)
  3. Owner can analyze payment method breakdown and peak hours
  4. Owner can review delivery performance metrics (average time, success rate)
  5. Owner can view revenue trends over time (daily, weekly, monthly charts)
**Plans**: TBD

Plans:
- [ ] 09-01: Sales and order analytics
- [ ] 09-02: Payment and delivery performance metrics
- [ ] 09-03: Revenue trends and dashboards

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | ✓ Complete | 2026-02-03 |
| 2. POS Core | 0/7 | Planned | - |
| 3. Inventory | 0/3 | Not started | - |
| 4. Payments | 0/4 | Not started | - |
| 5. Delivery | 0/4 | Not started | - |
| 6. WhatsApp | 0/4 | Not started | - |
| 7. Suppliers | 0/3 | Not started | - |
| 8. Finance | 0/3 | Not started | - |
| 9. Analytics | 0/3 | Not started | - |

**Total:** 3/34 plans complete

---
*Roadmap created: 2026-02-03*
*Last updated: 2026-02-03 (Phase 2 planned)*
