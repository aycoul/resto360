---
phase: 05-delivery
plan: 04
subsystem: ui
tags: [next.js, websocket, google-maps, real-time, tracking, pwa]

# Dependency graph
requires:
  - phase: 05-02
    provides: WebSocket consumers for delivery tracking
  - phase: 02-04
    provides: Next.js PWA foundation with next-intl
provides:
  - Customer delivery tracking page at /track/{delivery_id}
  - Real-time map with driver location via Google Maps
  - Driver info card with tel: and sms: contact links
  - Delivery status timeline with progress indicators
  - Public API endpoint for tracking data without auth
  - WebSocket hook for live location updates
affects: [06-whatsapp, 09-analytics]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Public tracking uses delivery ID as access key (no auth required)
    - WebSocket reconnection with exponential backoff 1s-30s
    - Google Maps loaded via script tag (lightweight, no npm package)

key-files:
  created:
    - apps/web/lib/api/delivery.ts
    - apps/web/lib/hooks/useDeliveryTracking.ts
    - apps/web/components/delivery/TrackingMap.tsx
    - apps/web/components/delivery/DriverInfo.tsx
    - apps/web/components/delivery/DeliveryTimeline.tsx
    - apps/web/components/delivery/DeliveryHeader.tsx
    - apps/web/app/[locale]/track/[id]/page.tsx
  modified:
    - apps/api/apps/delivery/views.py
    - apps/api/apps/delivery/urls.py

key-decisions:
  - "Delivery ID serves as access key for public tracking (no auth required)"
  - "Google Maps loaded via script tag instead of npm package (lighter weight)"
  - "tel: and sms: links for native mobile contact integration"

patterns-established:
  - "Public endpoints use AllowAny permission with ID-based access"
  - "WebSocket hook pattern with automatic reconnection and cleanup"
  - "Map component with marker updates for real-time tracking"

# Metrics
duration: 28min
completed: 2026-02-04
---

# Phase 5 Plan 4: Customer Tracking Page Summary

**Real-time delivery tracking PWA page with Google Maps, driver contact links, and WebSocket location updates**

## Performance

- **Duration:** 28 min
- **Started:** 2026-02-04T07:20:32Z
- **Completed:** 2026-02-04T07:48:35Z
- **Tasks:** 4 (3 auto + 1 checkpoint)
- **Files modified:** 9

## Accomplishments

- Customer can open tracking link and see delivery status in real-time
- Map shows driver location with automatic updates via WebSocket
- Driver info card with call and message buttons (tel:/sms: links)
- Delivery timeline shows progress through statuses (assigned -> delivered)
- Public API endpoint returns tracking data without authentication
- French and English translations added for error states

## Task Commits

Each task was committed atomically:

1. **Task 1: Create delivery tracking hook with WebSocket** - `bac7bc0` (feat)
2. **Task 2: Create tracking page components** - `8a7a2cf` (feat)
3. **Task 3: Create tracking page and public API endpoint** - `4c18d40` (feat)
4. **Task 4: Human verification** - Translations added by user - `aafa31e`

## Files Created/Modified

- `apps/web/lib/api/delivery.ts` - Delivery API client with getDeliveryInfo function
- `apps/web/lib/hooks/useDeliveryTracking.ts` - WebSocket hook for real-time location updates
- `apps/web/components/delivery/TrackingMap.tsx` - Google Maps component with driver/delivery markers
- `apps/web/components/delivery/DriverInfo.tsx` - Driver card with tel: and sms: contact links
- `apps/web/components/delivery/DeliveryTimeline.tsx` - Status progress timeline
- `apps/web/components/delivery/DeliveryHeader.tsx` - Order header with ETA display
- `apps/web/app/[locale]/track/[id]/page.tsx` - Customer tracking page
- `apps/api/apps/delivery/views.py` - Added DeliveryTrackingView with AllowAny permission
- `apps/api/apps/delivery/urls.py` - Added /track/{id}/ public endpoint

## Decisions Made

- **Delivery ID as access key**: No authentication required for tracking - the delivery UUID serves as the secret access token. This enables customers to track without creating accounts.
- **Google Maps via script tag**: Instead of @react-google-maps/api npm package, loaded Google Maps directly via script tag. This is lighter weight and avoids dependency issues.
- **Native contact links**: Used tel: and sms: protocol links for driver contact. These work natively on iOS and Android, opening the phone/messages app directly.

## Deviations from Plan

None - plan executed exactly as written.

Note: Plan referenced `apps/pwa` but actual directory is `apps/web`. Files were created in correct location.

## Issues Encountered

None - execution proceeded smoothly.

## User Setup Required

**Google Maps API key needed for map functionality.** Add to `.env.local`:
```
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_key_here
```

Without this key, the map will show "Loading map..." but markers won't appear.

## Next Phase Readiness

- Phase 5 (Delivery) complete with all 4 plans executed
- Customer tracking flow fully functional
- Ready for Phase 6 (WhatsApp) or Phase 9 (Analytics)

---
*Phase: 05-delivery*
*Completed: 2026-02-04*
