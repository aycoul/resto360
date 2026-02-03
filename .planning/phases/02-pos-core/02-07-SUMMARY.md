---
phase: 02-pos-core
plan: 07
subsystem: customer-ordering
tags: [qr-menu, public-api, self-ordering, mobile-first]

dependency_graph:
  requires:
    - 02-02: Orders backend
    - 02-04: Next.js PWA foundation
  provides:
    - Public menu API endpoint
    - Guest order creation
    - Customer-facing QR menu page
    - Self-service ordering flow
  affects:
    - 02-06: Payments integration
    - Phase 3: Kitchen display system

tech_stack:
  added: []
  patterns:
    - Public API with AllowAny permission
    - Guest order serializer for unauthenticated users
    - API to LocalModel type conversion
    - Bottom sheet modal pattern (mobile-first)

file_tracking:
  key_files:
    created:
      - apps/api/apps/menu/views.py (PublicMenuView, PublicOrderCreateView)
      - apps/api/apps/orders/serializers.py (GuestOrderCreateSerializer)
      - apps/web/lib/hooks/usePublicMenu.ts
      - apps/web/app/[locale]/menu/[slug]/layout.tsx
      - apps/web/app/[locale]/menu/[slug]/page.tsx
      - apps/web/components/menu/PublicMenuGrid.tsx
      - apps/web/components/menu/PublicMenuItemCard.tsx
      - apps/web/components/menu/PublicModifierModal.tsx
      - apps/web/components/menu/CustomerCart.tsx
      - apps/web/components/menu/CustomerCheckout.tsx
      - apps/web/components/menu/OrderConfirmation.tsx
    modified:
      - apps/api/apps/menu/urls.py

decisions:
  - id: public-api-no-auth
    choice: AllowAny permission with empty authentication_classes
    reason: Customer menu pages must be accessible without login
  - id: guest-order-serializer
    choice: Separate GuestOrderCreateSerializer from authenticated OrderCreateSerializer
    reason: Guest orders have different validation (no table lookup, no cashier)
  - id: table-in-notes
    choice: Store table info in notes field for guest orders
    reason: Guest orders don't have table foreign key lookup
  - id: mobile-bottom-sheet
    choice: Bottom sheet modals for cart and checkout
    reason: Better mobile UX than centered modals
  - id: type-conversion
    choice: Convert API MenuItem to LocalMenuItem for cart
    reason: Reuse cart store types and keep snake_case/camelCase boundary clear

metrics:
  duration: 7 minutes
  completed: 2026-02-03
---

# Phase 2 Plan 7: Customer QR Menu Summary

Public menu page with self-service ordering for customers scanning QR codes from their phones.

## What Was Built

### Backend: Public API Endpoints

**PublicMenuView** (`/api/v1/menu/public/{slug}/`)
- No authentication required (AllowAny permission)
- Returns restaurant info and full menu by slug
- Filters to visible categories and available items only
- Optimized with prefetch_related for nested modifiers

**PublicOrderCreateView** (`/api/v1/menu/public/{slug}/order/`)
- Creates guest orders without authentication
- Returns order number and estimated wait time (15 min default)
- Validates menu items belong to restaurant

**GuestOrderCreateSerializer**
- Validates guest order data (order_type, table, customer info, items)
- Creates order without cashier (null foreign key)
- Stores table number in notes field (no FK lookup for guests)
- Supports dine_in and takeout order types

### Frontend: Public Menu Page

**Page Structure**
- `/[locale]/menu/[slug]/` - Public menu URL pattern
- Layout wraps children with CartProvider
- Sticky header with restaurant name and locale switcher
- Category sections with sticky category names

**Menu Components**
- `PublicMenuGrid` - List of menu items for a category
- `PublicMenuItemCard` - Item card with thumbnail, name, description, price
- `PublicModifierModal` - Bottom sheet for modifier selection
- Converts API types (snake_case) to LocalMenuItem (camelCase)

**Cart & Checkout Components**
- `CustomerCart` - Bottom sheet with item list and quantity controls
- `CustomerCheckout` - Form for order type, table, customer name, phone
- `OrderConfirmation` - Success screen with order number and wait time
- Floating action button (FAB) shows cart total when items present

### UX Features

1. **Mobile-First Design**
   - Bottom sheet modals for native app feel
   - Sticky headers for context while scrolling
   - FAB for easy cart access from anywhere

2. **Modifier Selection**
   - Required modifier validation
   - Single and multi-select support
   - Price adjustment display (+/- XOF)
   - Running total updates in real-time

3. **Order Flow**
   - Browse menu by category
   - Add items to cart (with optional modifiers)
   - View/edit cart with quantity controls
   - Enter order details at checkout
   - See confirmation with order number

## API Contracts

### Public Menu Request
```
GET /api/v1/menu/public/{slug}/
No authentication required

Response 200:
{
  "restaurant": {
    "id": "uuid",
    "name": "Restaurant Name",
    "slug": "restaurant-slug",
    "address": "123 Main St",
    "phone": "+225..."
  },
  "categories": [
    {
      "id": "uuid",
      "name": "Category Name",
      "items": [...]
    }
  ]
}
```

### Public Order Creation
```
POST /api/v1/menu/public/{slug}/order/
No authentication required

Request:
{
  "order_type": "dine_in" | "takeout",
  "table": "Table 5",
  "customer_name": "John Doe",
  "customer_phone": "+225...",
  "items": [
    {
      "menu_item_id": "uuid",
      "quantity": 2,
      "modifiers": [
        { "modifier_option_id": "uuid" }
      ]
    }
  ]
}

Response 201:
{
  "id": "uuid",
  "order_number": 42,
  "status": "pending",
  "total": 5000,
  "estimated_wait": 15
}
```

## Commits

1. `e0e81b7` - feat(02-07): add public menu API endpoints
2. `ad97b57` - feat(02-07): add public menu page structure
3. `f7d996c` - feat(02-07): build public menu display components
4. `08eea22` - feat(02-07): build customer cart and checkout components

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Immediate Next Steps:**
- 02-06 (Payments) can integrate with guest orders
- QR code generation for restaurant menu URLs

**Integration Points:**
- Kitchen display will receive guest orders same as cashier orders
- Payment flow can extend checkout for prepayment option

**Known Limitations:**
- Estimated wait time is hardcoded (15 min)
- No real-time order status updates for customers
- No payment integration yet (pay at counter)
