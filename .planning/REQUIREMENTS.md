# Requirements: RESTO360

**Defined:** 2026-02-03
**Core Value:** Restaurants can take orders, accept payments, and manage deliveries — even when internet is unreliable.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Foundation (FOUND)

- [ ] **FOUND-01**: Multi-tenant database with restaurant isolation
- [ ] **FOUND-02**: JWT authentication with role-based permissions
- [ ] **FOUND-03**: User roles: owner, manager, cashier, kitchen, driver
- [ ] **FOUND-04**: Restaurant settings (name, address, timezone, currency)
- [ ] **FOUND-05**: CI/CD pipeline with automated testing
- [ ] **FOUND-06**: Development environment (Docker Compose)

### POS Core (POS)

- [ ] **POS-01**: Menu category management (create, edit, reorder, toggle visibility)
- [ ] **POS-02**: Menu item management (name, price, description, image, availability)
- [ ] **POS-03**: Menu item options/modifiers (size, extras, customizations)
- [ ] **POS-04**: Cart management (add, remove, adjust quantity, notes)
- [ ] **POS-05**: Order creation with order type (dine-in, takeout, delivery)
- [ ] **POS-06**: Table assignment for dine-in orders
- [ ] **POS-07**: Order number generation (unique per restaurant per day)
- [ ] **POS-08**: Kitchen display showing order queue by status
- [ ] **POS-09**: Order status updates (pending → preparing → ready → completed)
- [ ] **POS-10**: Receipt generation (PDF with order details)
- [ ] **POS-11**: Offline-first operation with IndexedDB queue
- [ ] **POS-12**: Background sync when connection restored
- [ ] **POS-13**: Multi-language UI (French/English toggle)
- [ ] **POS-14**: QR code menu for customers to view and order
- [ ] **POS-15**: Customer self-ordering from QR menu

### Inventory (INV)

- [ ] **INV-01**: Stock item management (name, SKU, current quantity, unit)
- [ ] **INV-02**: Stock movement tracking (in, out, adjustment with reason)
- [ ] **INV-03**: Low stock alerts (configurable threshold per item)
- [ ] **INV-04**: Menu item to ingredient mapping
- [ ] **INV-05**: Automatic stock deduction on order completion
- [ ] **INV-06**: Inventory reports (current stock, movement history)

### Payments (PAY)

- [ ] **PAY-01**: Wave Money payment initiation
- [ ] **PAY-02**: Wave Money webhook handling and status updates
- [ ] **PAY-03**: Orange Money payment initiation
- [ ] **PAY-04**: Orange Money webhook handling and status updates
- [ ] **PAY-05**: MTN MoMo payment initiation
- [ ] **PAY-06**: MTN MoMo webhook handling and status updates
- [ ] **PAY-07**: Cash payment recording with drawer tracking
- [ ] **PAY-08**: Payment status display (pending, success, failed)
- [ ] **PAY-09**: Idempotent payment requests (prevent double-charge)
- [ ] **PAY-10**: Daily payment reconciliation report
- [ ] **PAY-11**: Refund initiation (for mobile money)

### Delivery (DEL)

- [ ] **DEL-01**: Delivery zone configuration (polygon on map, fee, minimum order)
- [ ] **DEL-02**: Driver registration and profile management
- [ ] **DEL-03**: Driver availability toggle (online/offline)
- [ ] **DEL-04**: Automatic driver assignment (nearest available)
- [ ] **DEL-05**: Manual driver assignment override
- [ ] **DEL-06**: Delivery status tracking (assigned → picked up → en route → delivered)
- [ ] **DEL-07**: Real-time driver GPS location updates
- [ ] **DEL-08**: Estimated delivery time calculation
- [ ] **DEL-09**: Driver app: view assigned deliveries
- [ ] **DEL-10**: Driver app: navigation to pickup/delivery address
- [ ] **DEL-11**: Driver app: update delivery status
- [ ] **DEL-12**: Customer app: view order status
- [ ] **DEL-13**: Customer app: real-time delivery tracking on map
- [ ] **DEL-14**: Customer app: driver contact (call/message)
- [ ] **DEL-15**: Delivery confirmation with customer signature/photo

### WhatsApp (WA)

- [ ] **WA-01**: WhatsApp Business API integration (Twilio)
- [ ] **WA-02**: Webhook receiver for incoming messages
- [ ] **WA-03**: Menu display via WhatsApp (text or catalog)
- [ ] **WA-04**: Natural language order parsing (AI-powered)
- [ ] **WA-05**: Order confirmation with summary
- [ ] **WA-06**: Payment link generation and sending
- [ ] **WA-07**: Location capture for delivery address
- [ ] **WA-08**: Order status notifications (preparing, out for delivery, delivered)
- [ ] **WA-09**: Conversation history per customer
- [ ] **WA-10**: Template messages for common responses

### Suppliers (SUP)

- [ ] **SUP-01**: Supplier registration (name, contact, categories)
- [ ] **SUP-02**: Supplier product catalog
- [ ] **SUP-03**: Purchase order creation
- [ ] **SUP-04**: Purchase order status tracking (pending → confirmed → shipped → delivered)
- [ ] **SUP-05**: Automatic stock update on PO delivery
- [ ] **SUP-06**: Suggested reorders based on low stock
- [ ] **SUP-07**: Supplier invoice management
- [ ] **SUP-08**: Purchase history and reporting

### Embedded Finance (FIN)

- [ ] **FIN-01**: Daily/weekly/monthly sales aggregation
- [ ] **FIN-02**: Automated credit scoring based on sales history
- [ ] **FIN-03**: Business loan application flow
- [ ] **FIN-04**: Loan terms display (amount, interest, term, monthly payment)
- [ ] **FIN-05**: Loan approval/rejection workflow
- [ ] **FIN-06**: Loan disbursement via mobile money
- [ ] **FIN-07**: Repayment schedule tracking
- [ ] **FIN-08**: Cash advance application (simpler product)
- [ ] **FIN-09**: Cash advance: percentage of daily sales repayment
- [ ] **FIN-10**: Finance dashboard (active loans, repayment status)

### Analytics (ANA)

- [ ] **ANA-01**: Daily sales summary (revenue, order count, average order value)
- [ ] **ANA-02**: Item popularity report (top sellers, slow movers)
- [ ] **ANA-03**: Payment method breakdown
- [ ] **ANA-04**: Peak hours analysis
- [ ] **ANA-05**: Delivery performance metrics (avg time, success rate)
- [ ] **ANA-06**: Revenue trends (daily, weekly, monthly charts)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Features

- **ADV-01**: Loyalty/rewards program for repeat customers
- **ADV-02**: Promotions and discount codes
- **ADV-03**: Multi-branch support (one owner, multiple locations)
- **ADV-04**: Franchise management
- **ADV-05**: Kitchen display system with ticket printing
- **ADV-06**: Staff scheduling and time tracking

### Integrations

- **INT-01**: Accounting software integration (QuickBooks, etc.)
- **INT-02**: Card payments (Visa/Mastercard) via aggregator
- **INT-03**: POS hardware integration (receipt printer, cash drawer)
- **INT-04**: Delivery aggregators (Glovo, Jumia Food)

### Scale

- **SCL-01**: Multi-country support (currency, tax, language)
- **SCL-02**: White-label platform for enterprise clients
- **SCL-03**: API for third-party integrations

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Card payments (Visa/MC) | Mobile money is 95%+ of transactions in target market |
| Multi-country v1 | Focus on Côte d'Ivoire, expand after validation |
| Native iOS/Android POS | PWA sufficient for tablets, reduces maintenance |
| Real-time chat support | WhatsApp handles customer communication |
| Tip collection | Not common practice in target market |
| Reservation system | Table management is walk-in focused |
| Calorie/nutrition info | Not required by local regulations |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 to FOUND-06 | Phase 1 | Pending |
| POS-01 to POS-15 | Phase 2 | Pending |
| INV-01 to INV-06 | Phase 3 | Pending |
| PAY-01 to PAY-11 | Phase 4 | Pending |
| DEL-01 to DEL-15 | Phase 5 | Pending |
| WA-01 to WA-10 | Phase 6 | Pending |
| SUP-01 to SUP-08 | Phase 7 | Pending |
| FIN-01 to FIN-10 | Phase 8 | Pending |
| ANA-01 to ANA-06 | Phase 9 | Pending |

**Coverage:**
- v1 requirements: 81 total
- Mapped to phases: 81
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-03*
*Last updated: 2026-02-03 after initial definition*
