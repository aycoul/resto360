---
phase: 02-pos-core
plan: 01
subsystem: api
tags: [django, drf, menu, models, multi-tenant, imagekit]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: TenantModel, TenantManager, permissions, User model
provides:
  - Category, MenuItem, Modifier, ModifierOption models
  - Menu API endpoints at /api/v1/menu/
  - Nested serializers for full menu retrieval
  - TenantContextMixin for DRF views
  - TenantModelViewSet base class
affects: [02-02-orders, 02-03-kitchen-display, 02-05-pos-ui]

# Tech tracking
tech-stack:
  added:
    - django-imagekit>=5.0
    - Pillow>=10.0
    - drf-writable-nested>=0.7.0
  patterns:
    - TenantContextMixin for DRF tenant context
    - all_objects manager for related lookups
    - get_queryset() for fresh querysets (not class-level)

key-files:
  created:
    - apps/api/apps/menu/models.py
    - apps/api/apps/menu/serializers.py
    - apps/api/apps/menu/views.py
    - apps/api/apps/menu/urls.py
    - apps/api/apps/menu/admin.py
    - apps/api/apps/core/views.py
  modified:
    - apps/api/requirements/base.txt
    - apps/api/config/settings/base.py
    - apps/api/config/urls.py
    - apps/api/apps/core/middleware.py

key-decisions:
  - "Use all_objects as default manager for related lookups (unfiltered)"
  - "Create TenantContextMixin to set context after DRF authentication"
  - "Avoid class-level queryset= in viewsets (evaluated at class load without context)"
  - "XOF prices stored as integers (no decimals for CFA franc)"
  - "ImageKit for thumbnail generation (300x300 JPEG 85% quality)"

patterns-established:
  - "TenantModelViewSet: Base class for all tenant-aware DRF viewsets"
  - "TenantContextMixin: Sets tenant context in initial(), clears in finalize_response()"
  - "Model managers: all_objects (first, unfiltered), objects (TenantManager, filtered)"
  - "ViewSet querysets: Always create in get_queryset(), never class-level"

# Metrics
duration: 22min
completed: 2026-02-03
---

# Phase 02 Plan 01: Menu Models & API Summary

**Full menu management backend with Category, MenuItem, Modifier, ModifierOption models using TenantModel inheritance, DRF viewsets, and nested serializers for single-request menu retrieval**

## Performance

- **Duration:** 22 min
- **Started:** 2026-02-03T19:40:13Z
- **Completed:** 2026-02-03T20:01:51Z
- **Tasks:** 4
- **Files modified:** 13

## Accomplishments
- Category, MenuItem, Modifier, ModifierOption models with full tenant isolation
- REST API at /api/v1/menu/ with CRUD for all entities
- Nested serializers return complete menu in single request via /api/v1/menu/full/
- TenantContextMixin solves DRF authentication timing issue
- 40 comprehensive tests covering models, API, and multi-tenant isolation

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies and create menu app structure** - `f4d06df` (feat)
2. **Task 2: Create menu models with tenant isolation** - `d4c3864` (feat)
3. **Task 3: Create serializers and API endpoints** - `7b50051` (feat)
4. **Task 4: Create comprehensive tests** - `b610e43` (test)

## Files Created/Modified
- `apps/api/apps/menu/models.py` - Category, MenuItem, Modifier, ModifierOption with TenantModel
- `apps/api/apps/menu/serializers.py` - Nested read serializers, write serializers with validation
- `apps/api/apps/menu/views.py` - ViewSets using TenantModelViewSet, FullMenuView
- `apps/api/apps/menu/urls.py` - Router registration for all endpoints
- `apps/api/apps/menu/admin.py` - Admin with inline editing
- `apps/api/apps/core/views.py` - TenantContextMixin and TenantModelViewSet
- `apps/api/requirements/base.txt` - Added imagekit, Pillow, drf-writable-nested
- `apps/api/config/settings/base.py` - Added menu app, imagekit, media settings
- `apps/api/config/urls.py` - Registered /api/v1/menu/ routes

## Decisions Made

1. **TenantContextMixin pattern:** DRF authentication happens at view level (not middleware), so tenant context must be set in view's `initial()` method after authentication completes.

2. **Dual managers pattern:** `all_objects = models.Manager()` as first manager for Django's default manager (used in related lookups), `objects = TenantManager()` for filtered queries. This prevents tenant filtering on related object access.

3. **Fresh querysets in get_queryset():** Class-level `queryset = Model.objects.all()` is evaluated at class load time when there's no tenant context. Moving queryset creation into `get_queryset()` ensures it's evaluated during the request with proper context.

4. **Integer prices for XOF:** CFA franc has no decimal places, so `PositiveIntegerField` is appropriate and avoids floating point issues.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] TenantManager not filtering in DRF views**
- **Found during:** Task 4 (test verification)
- **Issue:** Multi-tenant isolation tests failing - API returning all restaurants' data
- **Root cause:** DRF authentication happens at view level, after Django middleware. TenantMiddleware was setting context before authentication, so `request.user` was `AnonymousUser`.
- **Fix:** Created `TenantContextMixin` that sets context in `initial()` (called after DRF authentication), and clears it in `finalize_response()`.
- **Files created:** apps/api/apps/core/views.py
- **Verification:** All 40 tests pass including 3 multi-tenant isolation tests
- **Committed in:** b610e43

**2. [Rule 3 - Blocking] Class-level queryset evaluated without context**
- **Found during:** Task 4 (debugging test failures)
- **Issue:** `queryset = Category.objects.all()` at class level creates queryset when Python loads the class, at which time there's no tenant context.
- **Fix:** Remove class-level `queryset` attribute, create fresh queryset in `get_queryset()` method.
- **Files modified:** apps/api/apps/menu/views.py
- **Verification:** SQL queries now include `WHERE restaurant_id = ...`
- **Committed in:** b610e43

**3. [Rule 3 - Blocking] Related managers using TenantManager**
- **Found during:** Task 4 (model relationship tests)
- **Issue:** `category.items.all()` was returning empty queryset because TenantManager filtered without context.
- **Fix:** Added `all_objects = models.Manager()` as first manager on all menu models. Django uses first defined manager as default for related lookups.
- **Files modified:** apps/api/apps/menu/models.py
- **Verification:** Model relationship tests pass
- **Committed in:** b610e43 (part of Task 2 model changes)

---

**Total deviations:** 3 auto-fixed (all Rule 3 - Blocking)
**Impact on plan:** All fixes necessary for correct tenant isolation. No scope creep. This establishes critical patterns for all future DRF viewsets.

## Issues Encountered
- None during planned work - all issues were architectural discoveries during testing.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Menu models ready for Order model relationships (02-02-orders)
- API patterns established for future viewsets
- TenantModelViewSet available for all tenant-aware endpoints

---
*Phase: 02-pos-core*
*Completed: 2026-02-03*
