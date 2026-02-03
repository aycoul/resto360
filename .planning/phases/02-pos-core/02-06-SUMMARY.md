---
phase: 02-pos-core
plan: 06
subsystem: frontend
tags: [next.js, websocket, real-time, kitchen-display, react-hooks, web-audio]

# Dependency graph
requires:
  - phase: 02-03
    provides: WebSocket endpoint at ws://host/ws/kitchen/{restaurant_id}/?token={jwt}
  - phase: 02-04
    provides: Next.js PWA foundation, i18n, API client, Button component
provides:
  - Kitchen display page at /[locale]/kitchen
  - useKitchenSocket hook for WebSocket connection with auto-reconnect
  - useKitchenQueue hook for order state management
  - Real-time order queue components (OrderQueue, OrderStatusColumn, OrderCard)
affects: [03-01, 03-02]  # Mobile kitchen app, analytics dashboard

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useRef for WebSocket instance management"
    - "Web Audio API for sound notifications (no external files)"
    - "Exponential backoff for WebSocket reconnection"
    - "Optimistic updates with delayed order removal"

key-files:
  created:
    - apps/web/lib/hooks/useKitchenSocket.ts
    - apps/web/lib/hooks/useKitchenQueue.ts
    - apps/web/app/[locale]/kitchen/layout.tsx
    - apps/web/app/[locale]/kitchen/page.tsx
    - apps/web/components/kitchen/OrderQueue.tsx
    - apps/web/components/kitchen/OrderStatusColumn.tsx
    - apps/web/components/kitchen/OrderCard.tsx
  modified: []

key-decisions:
  - "Web Audio API beep instead of MP3 file - no external audio dependency"
  - "2-second delay before removing completed orders - visual confirmation"
  - "Exponential backoff 1s-30s for WebSocket reconnection"
  - "useRef for timeout tracking to prevent memory leaks"

patterns-established:
  - "Kitchen display pattern: status columns with order cards"
  - "WebSocket hook returns { isConnected, error, sendStatusUpdate, reconnect }"
  - "Queue hook returns filtered orders by status + handlers for socket events"

# Metrics
duration: 6min
completed: 2026-02-03
---

# Phase 02 Plan 06: Kitchen Display Frontend Summary

**Real-time kitchen order queue with WebSocket connection, status columns, sound notifications, and auto-removal of completed orders**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-03
- **Tasks:** 4
- **Files created:** 7
- **Files modified:** 0

## Accomplishments

- WebSocket connection hook with JWT authentication via query string
- Auto-reconnection with exponential backoff (1s to 30s max)
- Order queue state management with status filtering
- Kitchen display page with dark theme and live clock
- Three-column layout: Pending (yellow), Preparing (blue), Ready (green)
- Order cards with number, type, table, items, modifiers, notes, time
- Sound notification on new order (Web Audio API beep)
- Completed orders removed from display after 2-second confirmation delay

## Task Commits

Each task was committed atomically:

1. **Task 1: WebSocket and queue hooks** - `6ccc2ae` (feat)
2. **Task 2: Kitchen page and layout** - `82fe427` (feat)
3. **Task 3: Order queue components** - `3551cc6` (feat)
4. **Task 4: Sound and completed order removal** - `3124875` (feat)

## Files Created

### Hooks
- `apps/web/lib/hooks/useKitchenSocket.ts` - WebSocket connection with reconnect
- `apps/web/lib/hooks/useKitchenQueue.ts` - Order state management with sound

### Pages
- `apps/web/app/[locale]/kitchen/layout.tsx` - Dark theme layout
- `apps/web/app/[locale]/kitchen/page.tsx` - Kitchen display with WebSocket

### Components
- `apps/web/components/kitchen/OrderQueue.tsx` - Three-column container
- `apps/web/components/kitchen/OrderStatusColumn.tsx` - Colored status column
- `apps/web/components/kitchen/OrderCard.tsx` - Order details and actions

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Sound notification | Web Audio API beep | No external file needed, works offline |
| Completed order delay | 2 seconds | Visual confirmation before removal |
| Reconnect strategy | Exponential backoff | Prevents server overload on failures |
| Status type safety | Union types | Compile-time validation of status values |

## WebSocket Integration

### Connection
```typescript
const { isConnected, error, sendStatusUpdate, reconnect } = useKitchenSocket({
  restaurantId: '...',
  onInitialQueue: handleInitialQueue,
  onOrderCreated: handleOrderCreated,
  onOrderUpdated: handleOrderUpdated,
  onStatusChanged: handleStatusChanged,
});
```

### Message Handling
- `initial_queue` - Populates initial order list
- `order_created` - Adds new order, plays sound
- `order_updated` - Updates existing order
- `order_status_changed` - Updates status, removes if completed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed useRef TypeScript error**
- **Found during:** Task 1 verification
- **Issue:** `useRef<ReturnType<typeof setTimeout>>()` requires initial value in strict mode
- **Fix:** Changed to `useRef<ReturnType<typeof setTimeout> | null>(null)`
- **Files modified:** apps/web/lib/hooks/useKitchenSocket.ts
- **Commit:** 6ccc2ae

**2. [Rule 1 - Bug] Fixed status type mismatch**
- **Found during:** Task 3 verification
- **Issue:** `string` type incompatible with union type in callback
- **Fix:** Updated prop types to use `'preparing' | 'ready' | 'completed'`
- **Files modified:** OrderStatusColumn.tsx, OrderCard.tsx
- **Commit:** 3551cc6

## Issues Encountered

- Pre-existing build errors in menu pages (unrelated to this plan)
- Kitchen files compile correctly independently

## Verification Results

| Check | Status |
|-------|--------|
| TypeScript compiles (kitchen files) | PASS |
| useKitchenSocket hook exports | PASS |
| useKitchenQueue hook exports | PASS |
| Kitchen page at /[locale]/kitchen | PASS |
| OrderQueue with three columns | PASS |
| OrderCard with status actions | PASS |
| French/English translations | PASS |

## User Setup Required

- Backend WebSocket server must be running for real-time updates
- JWT authentication token required for WebSocket connection
- NEXT_PUBLIC_WS_URL environment variable for production

## Next Phase Readiness

- Mobile kitchen app (Phase 3) can reuse useKitchenQueue hook logic
- Same WebSocket protocol works across web and mobile
- Components ready for integration with real backend data

---
*Phase: 02-pos-core*
*Completed: 2026-02-03*
