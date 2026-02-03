---
phase: 02-pos-core
plan: 05
subsystem: ui
tags: [react, pwa, indexeddb, dexie, offline-first, tanstack-query, next-intl]

# Dependency graph
requires:
  - phase: 02-01
    provides: Menu backend API with categories, items, modifiers
  - phase: 02-02
    provides: Orders backend API with item creation
  - phase: 02-04
    provides: Next.js PWA foundation with IndexedDB schema, API client, sync utilities
provides:
  - POS cashier interface at /[locale]/pos
  - useMenu hook for offline-capable menu data
  - useCart hook for cart state management
  - createOfflineOrder for offline-first order creation
  - Complete checkout flow with modifier selection
affects: [02-06-payments, 02-03-kitchen-display, 03-mobile]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - React Context + useReducer for local state (cart)
    - useLiveQuery for reactive IndexedDB reads
    - Offline-first with optimistic UI

key-files:
  created:
    - apps/web/lib/hooks/useMenu.ts
    - apps/web/lib/hooks/useCart.ts
    - apps/web/lib/hooks/useOrders.ts
    - apps/web/lib/store/cartStore.tsx
    - apps/web/lib/db/operations.ts
    - apps/web/app/[locale]/pos/layout.tsx
    - apps/web/app/[locale]/pos/page.tsx
    - apps/web/components/pos/CategoryTabs.tsx
    - apps/web/components/pos/MenuGrid.tsx
    - apps/web/components/pos/MenuItemCard.tsx
    - apps/web/components/pos/Cart.tsx
    - apps/web/components/pos/CartItem.tsx
    - apps/web/components/pos/ModifierModal.tsx
    - apps/web/components/pos/OrderTypeSelector.tsx
    - apps/web/components/pos/CheckoutModal.tsx
  modified: []

key-decisions:
  - "React Context for cart state vs Zustand - simpler, no external dependency"
  - "Offline-first order creation with pending ops queue"
  - "XOF currency formatting with toLocaleString()"

patterns-established:
  - "POS component pattern: page -> layout(provider) -> grid -> cards"
  - "Offline data hook pattern: useQuery + useLiveQuery together"
  - "Cart state via Context/useReducer with computed values"

# Metrics
duration: 5min
completed: 2026-02-03
---

# Phase 02 Plan 05: POS Cashier Interface Summary

**Offline-first POS cashier interface with menu grid, cart management, modifier selection, and local order creation using IndexedDB and React Context**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-03T20:20:50Z
- **Completed:** 2026-02-03T20:25:43Z
- **Tasks:** 4
- **Files modified:** 16

## Accomplishments
- POS page displaying menu categories with item counts
- Menu items with modifier selection modal (required/optional, max selections, price adjustments)
- Cart with real-time totals, quantity controls, clear/checkout actions
- Order type selection (dine-in/takeout/delivery) with context-sensitive fields
- Offline-first order creation storing to IndexedDB first, queueing sync operation
- Reactive UI using Dexie's useLiveQuery for local data

## Task Commits

Each task was committed atomically:

1. **Task 1: Create menu data hooks with offline support** - `f7d76f0` (feat)
2. **Task 2: Create cart state management** - `2008a92` (feat)
3. **Task 3: Build POS page and components** - `0113c13` (feat)
4. **Task 4: Build modifier modal, checkout flow, order hooks** - `fd0465a` (feat)

## Files Created/Modified

**Hooks:**
- `apps/web/lib/hooks/useMenu.ts` - Fetches menu from API, syncs to IndexedDB, reactive reads
- `apps/web/lib/hooks/useCart.ts` - Cart operations: add, remove, update, computed totals
- `apps/web/lib/hooks/useOrders.ts` - Reactive access to local orders by status

**State Management:**
- `apps/web/lib/store/cartStore.tsx` - CartProvider context with useReducer
- `apps/web/lib/db/operations.ts` - createOfflineOrder, syncPendingOrders

**Pages:**
- `apps/web/app/[locale]/pos/layout.tsx` - CartProvider wrapper
- `apps/web/app/[locale]/pos/page.tsx` - Main POS page with menu grid + cart

**Components:**
- `apps/web/components/pos/CategoryTabs.tsx` - Horizontal category selection
- `apps/web/components/pos/MenuGrid.tsx` - Responsive item grid
- `apps/web/components/pos/MenuItemCard.tsx` - Clickable item with price
- `apps/web/components/pos/Cart.tsx` - Cart with totals and checkout
- `apps/web/components/pos/CartItem.tsx` - Item with quantity controls
- `apps/web/components/pos/ModifierModal.tsx` - Modifier selection modal
- `apps/web/components/pos/OrderTypeSelector.tsx` - Order type buttons
- `apps/web/components/pos/CheckoutModal.tsx` - Checkout form with confirmation

## Decisions Made
- **React Context for cart** - Used Context + useReducer instead of Zustand since cart state is localized to POS page tree and doesn't need persistence
- **Offline-first order flow** - Orders stored in IndexedDB immediately, pendingOps queue triggers sync when online
- **XOF formatting** - Using toLocaleString() for currency display (no decimals for CFA franc)
- **Modifier validation** - Client-side validation for required modifiers before cart add

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None - all components built and TypeScript compilation passed without issues.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- POS interface complete and ready for payment integration (02-06)
- Menu data flows from backend API through offline cache to UI
- Orders created locally can be viewed in kitchen display (02-03)
- Sync mechanism ready for when backend is connected

---
*Phase: 02-pos-core*
*Completed: 2026-02-03*
