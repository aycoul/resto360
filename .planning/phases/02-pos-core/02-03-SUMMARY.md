---
phase: 02-pos-core
plan: 03
subsystem: api
tags: [django, channels, websocket, redis, real-time, kitchen-display]

# Dependency graph
requires:
  - phase: 02-02
    provides: Order models, OrderSerializer, status transitions
provides:
  - WebSocket endpoint for kitchen display real-time updates
  - JWT authentication for WebSocket connections
  - Signal functions for broadcasting order events
  - Multi-tenant WebSocket isolation
affects: [02-06, 03-01, 03-02]  # Analytics, mobile kitchen, delivery tracking

# Tech tracking
tech-stack:
  added: [channels>=4.3.2, channels-redis>=4.2, daphne>=4.1, pytest-asyncio>=0.23]
  patterns:
    - "AsyncWebsocketConsumer with database_sync_to_async"
    - "JWTAuthMiddleware for WebSocket token authentication"
    - "Channel layer group_send for multi-client broadcasting"
    - "ProtocolTypeRouter for HTTP/WebSocket routing"

key-files:
  created:
    - apps/api/apps/orders/consumers.py
    - apps/api/apps/orders/routing.py
    - apps/api/apps/orders/middleware.py
    - apps/api/apps/orders/signals.py
    - apps/api/apps/orders/tests/test_consumers.py
    - apps/api/apps/orders/tests/test_signals.py
  modified:
    - apps/api/requirements/base.txt
    - apps/api/requirements/development.txt
    - apps/api/config/settings/base.py
    - apps/api/config/settings/testing.py
    - apps/api/config/asgi.py
    - apps/api/apps/orders/views.py

key-decisions:
  - "JWT via query string for WebSocket auth (browsers can't set headers)"
  - "InMemoryChannelLayer for testing (no Redis required in tests)"
  - "Explicit signal functions (not Django signals) for control and testability"
  - "Send initial queue on connect for immediate kitchen display population"

patterns-established:
  - "database_sync_to_async for ORM operations in async consumers"
  - "Channel groups named kitchen_{restaurant_id} for multi-tenant isolation"
  - "Message types map to consumer methods (order_created -> order_created())"

# Metrics
duration: 8min
completed: 2026-02-03
---

# Phase 02 Plan 03: Kitchen WebSocket Summary

**Django Channels WebSocket for real-time kitchen display with JWT auth and multi-tenant order broadcasting**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-03
- **Tasks:** 4
- **Files created:** 6
- **Files modified:** 6

## Accomplishments

- Django Channels configured with Redis channel layer (daphne ASGI server)
- KitchenConsumer WebSocket consumer at `/ws/kitchen/{restaurant_id}/`
- JWT authentication via query string parameter (`?token=xxx`)
- Multi-tenant isolation: users can only connect to their restaurant's kitchen
- Signal functions broadcast order events to all connected kitchen displays
- Initial queue sent on connect (pending/preparing/ready orders)
- 26 comprehensive tests (14 consumer + 12 signal)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Django Channels and configure ASGI** - `a87fa9a` (feat)
2. **Task 2: Create WebSocket consumer and routing** - `c92a5fc` (feat)
3. **Task 3: Create signals and wire to views** - `ba8e04a` (feat)
4. **Task 4: Create WebSocket tests** - `d99fc7b` (test)

## Files Created/Modified

### Created
- `apps/api/apps/orders/consumers.py` - KitchenConsumer WebSocket consumer
- `apps/api/apps/orders/routing.py` - WebSocket URL patterns
- `apps/api/apps/orders/middleware.py` - JWTAuthMiddleware for token auth
- `apps/api/apps/orders/signals.py` - Order event broadcast functions
- `apps/api/apps/orders/tests/test_consumers.py` - 14 WebSocket tests
- `apps/api/apps/orders/tests/test_signals.py` - 12 signal tests

### Modified
- `apps/api/requirements/base.txt` - Added channels, channels-redis, daphne
- `apps/api/requirements/development.txt` - Added pytest-asyncio
- `apps/api/config/settings/base.py` - ASGI_APPLICATION, CHANNEL_LAYERS
- `apps/api/config/settings/testing.py` - InMemoryChannelLayer
- `apps/api/config/asgi.py` - ProtocolTypeRouter with WebSocket support
- `apps/api/apps/orders/views.py` - Wire notify functions to order operations

## Decisions Made

1. **JWT via query string** - WebSocket API doesn't support custom headers in browsers
2. **Explicit signal functions** - More control and easier to test than Django signals
3. **InMemoryChannelLayer for tests** - No Redis dependency in test environment
4. **Initial queue on connect** - Kitchen display immediately shows current orders

## WebSocket API

### Connection
```
ws://host/ws/kitchen/{restaurant_id}/?token={jwt_access_token}
```

### Message Types (Server to Client)
```json
{"type": "initial_queue", "orders": [...]}
{"type": "order_created", "order": {...}}
{"type": "order_updated", "order": {...}}
{"type": "order_status_changed", "order_id": "...", "status": "...", "previous_status": "..."}
```

### Message Types (Client to Server)
```json
{"type": "update_status", "order_id": "...", "status": "preparing"}
```

### Close Codes
- 4001: Not authenticated
- 4003: Wrong restaurant (multi-tenant violation)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- None - Docker/Redis not required for code creation

## User Setup Required

- Redis must be running for production WebSocket functionality
- REDIS_URL environment variable should point to Redis instance (default: redis://localhost:6379/1)

## Next Phase Readiness

- Kitchen display frontend can connect to WebSocket (02-06 Kitchen UI)
- Order creation and status updates broadcast to all kitchen clients
- Real-time updates ready for mobile kitchen app (Phase 3)
- Same pattern can be extended for delivery tracking WebSocket

---
*Phase: 02-pos-core*
*Completed: 2026-02-03*
