---
phase: 02-pos-core
plan: 04
subsystem: frontend
tags: [next.js, pwa, i18n, offline-first, dexie, react-query]
depends_on:
  requires: [01-foundation]
  provides: [next.js-pwa, i18n-routing, offline-storage, api-client]
  affects: [02-05-pos-interface, 02-06-kitchen-display, 02-07-qr-menu]
tech_stack:
  added: [next.js-16, next-intl-4, dexie-4, tanstack-react-query-5, ducanh2912-next-pwa]
  patterns: [offline-first, locale-routing, operation-based-sync]
key_files:
  created:
    - apps/web/package.json
    - apps/web/next.config.ts
    - apps/web/middleware.ts
    - apps/web/i18n/routing.ts
    - apps/web/i18n/request.ts
    - apps/web/messages/fr.json
    - apps/web/messages/en.json
    - apps/web/lib/db/schema.ts
    - apps/web/lib/db/sync.ts
    - apps/web/lib/api/client.ts
    - apps/web/lib/api/types.ts
    - apps/web/lib/hooks/useOnlineStatus.ts
    - apps/web/components/providers/QueryProvider.tsx
    - apps/web/components/ui/OfflineIndicator.tsx
    - apps/web/components/ui/LocaleSwitcher.tsx
    - apps/web/components/ui/Button.tsx
    - apps/web/app/layout.tsx
    - apps/web/app/[locale]/layout.tsx
    - apps/web/app/[locale]/page.tsx
    - apps/web/public/manifest.json
  modified:
    - .gitignore
decisions:
  - id: nextjs-16
    choice: Next.js 16.1.6 with Turbopack
    rationale: Latest stable version, App Router, excellent DX
  - id: pwa-library
    choice: "@ducanh2912/next-pwa"
    rationale: Maintained fork, App Router support, workbox integration
  - id: i18n-library
    choice: next-intl v4
    rationale: Best Next.js App Router integration, type-safe translations
  - id: french-default
    choice: French as default locale
    rationale: Target market is Ivory Coast, French-speaking
metrics:
  duration: ~15 minutes
  completed: 2026-02-03
---

# Phase 02 Plan 04: Next.js PWA Foundation Summary

**One-liner:** Offline-first Next.js 16 PWA with French/English i18n, Dexie IndexedDB, and JWT-authenticated API client.

## What Was Built

### Task 1: Next.js Project with PWA Configuration
- Initialized Next.js 16.1.6 with TypeScript, Tailwind CSS, ESLint
- Installed core dependencies: dexie, next-intl, @ducanh2912/next-pwa, @tanstack/react-query
- Configured PWA with manifest.json and service worker (disabled in dev)
- Added API proxy rewrite for localhost:8000 backend
- Created placeholder icons (192x192, 512x512)

### Task 2: i18n with next-intl (French/English)
- Created routing.ts with French as default locale, localePrefix: "always"
- Implemented middleware.ts for locale routing
- Added comprehensive translations for POS, kitchen, and offline states
- Created [locale] layout with NextIntlClientProvider
- Implemented locale-aware home page with language switcher

### Task 3: Dexie IndexedDB Schema and API Client
- Defined RestaurantDB class with 5 tables:
  - categories: Menu categories with display order
  - menuItems: Items with modifiers
  - orders: Local orders with sync status
  - pendingOps: Sync queue with retry logic
  - syncMeta: Last sync timestamps
- Implemented sync queue operations (queue, mark syncing/synced/failed)
- Created TypeScript interfaces matching backend API (Category, MenuItem, Order)
- Built authenticated API client with automatic JWT refresh
- Added useOnlineStatus hook for connectivity detection

### Task 4: Shared Components and Providers
- QueryProvider: TanStack Query with offline-friendly defaults
- OfflineIndicator: Shows offline status and pending operations count
- LocaleSwitcher: FR/EN toggle buttons
- Button: Reusable button with variants (primary, secondary, danger, ghost)

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Next.js version | 16.1.6 | Latest stable with Turbopack |
| PWA library | @ducanh2912/next-pwa | Maintained, App Router support |
| i18n library | next-intl v4 | Type-safe, excellent App Router integration |
| Default locale | French | Target market is francophone West Africa |
| Offline storage | Dexie 4.x | Best IndexedDB wrapper, React hooks support |
| Server state | TanStack Query v5 | Offline-friendly, mutation queuing |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed PWA config TypeError**
- **Found during:** Task 1 verification
- **Issue:** `skipWaiting` option moved to `workboxOptions` in newer @ducanh2912/next-pwa
- **Fix:** Moved `skipWaiting: true` under `workboxOptions` object
- **Files modified:** apps/web/next.config.ts

**2. [Rule 3 - Blocking] Fixed .gitignore lib/ exclusion**
- **Found during:** Task 3 commit
- **Issue:** Root .gitignore had `lib/` which excluded apps/web/lib
- **Fix:** Changed to `/lib/` to only exclude root-level lib directory
- **Files modified:** .gitignore

## Commits

| Hash | Message |
|------|---------|
| b3e5f9a | feat(02-04): create Next.js project with PWA and i18n packages |
| 5973743 | feat(02-04): configure i18n with next-intl (French/English) |
| 0fdf200 | feat(02-04): create Dexie IndexedDB schema and API client |
| a10155b | feat(02-04): create shared components and providers |

## Verification Results

| Check | Status |
|-------|--------|
| npm run dev starts at localhost:3000 | PASS |
| npm run build completes | PASS |
| /fr shows French content | PASS |
| /en shows English content | PASS |
| LocaleSwitcher component exists | PASS |
| OfflineIndicator with Dexie query | PASS |
| No TypeScript errors | PASS |

## Files Created

```
apps/web/
├── app/
│   ├── layout.tsx              # Root layout with manifest
│   ├── globals.css             # Tailwind styles
│   └── [locale]/
│       ├── layout.tsx          # Locale layout with providers
│       └── page.tsx            # Home page with translations
├── components/
│   ├── providers/
│   │   └── QueryProvider.tsx   # TanStack Query setup
│   └── ui/
│       ├── Button.tsx          # Reusable button
│       ├── LocaleSwitcher.tsx  # FR/EN toggle
│       └── OfflineIndicator.tsx # Offline status badge
├── i18n/
│   ├── routing.ts              # Locale configuration
│   └── request.ts              # Server-side i18n config
├── lib/
│   ├── api/
│   │   ├── client.ts           # Authenticated fetch wrapper
│   │   └── types.ts            # API response interfaces
│   ├── db/
│   │   ├── schema.ts           # Dexie database definition
│   │   └── sync.ts             # Sync queue operations
│   └── hooks/
│       └── useOnlineStatus.ts  # Online/offline hook
├── messages/
│   ├── en.json                 # English translations
│   └── fr.json                 # French translations
├── public/
│   ├── manifest.json           # PWA manifest
│   ├── icon-192.png            # PWA icon
│   └── icon-512.png            # PWA icon
├── middleware.ts               # i18n routing middleware
├── next.config.ts              # Next.js + PWA config
├── package.json                # Dependencies
└── tsconfig.json               # TypeScript config
```

## Next Phase Readiness

**Ready for:**
- 02-05: POS cashier interface can use Dexie for offline orders, API client for sync
- 02-06: Kitchen display can use locale routing and translations
- 02-07: Customer QR menu can leverage i18n and offline capability

**Blockers:** None

**Notes:**
- The middleware.ts deprecation warning is cosmetic (Next.js 16 transition)
- PWA service worker is disabled in development mode for better DX
- Placeholder icons should be replaced with branded versions before production
