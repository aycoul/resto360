---
phase: 01-foundation
plan: 02
subsystem: auth
tags: [jwt, django, drf, multi-tenant, permissions, phone-auth, xof]

# Dependency graph
requires:
  - phase: 01-foundation/01
    provides: Django project structure with settings, DRF, SimpleJWT configured
provides:
  - Custom User model with phone as username
  - Restaurant model for multi-tenant architecture
  - TenantMiddleware for automatic tenant context
  - TenantManager for automatic query filtering
  - Role-based permission classes (IsOwner, IsOwnerOrManager, IsCashier, IsSameRestaurant)
  - JWT authentication with custom claims (role, restaurant_id, permissions)
  - Owner registration creating user + restaurant atomically
  - Staff invite with role-based access control
affects: [02-menu, 03-orders, 04-payments, 05-delivery]

# Tech tracking
tech-stack:
  added: [pytest-factoryboy, pyjwt (for test decoding)]
  patterns: [contextvars for tenant isolation, abstract base models with UUID]

key-files:
  created:
    - apps/api/apps/core/models.py
    - apps/api/apps/core/context.py
    - apps/api/apps/core/managers.py
    - apps/api/apps/core/middleware.py
    - apps/api/apps/core/permissions.py
    - apps/api/apps/authentication/models.py
    - apps/api/apps/authentication/serializers.py
    - apps/api/apps/authentication/views.py
    - apps/api/apps/authentication/urls.py
  modified:
    - apps/api/config/settings/base.py
    - apps/api/config/urls.py
    - apps/api/config/settings/testing.py

key-decisions:
  - "Phone number as username (Ivory Coast market - phone-first)"
  - "UUID primary keys on all models for better distribution"
  - "contextvars for thread-safe tenant context (async-compatible)"
  - "XOF currency and Africa/Abidjan timezone defaults"
  - "Role-based permissions: owner > manager > cashier > kitchen/driver"

patterns-established:
  - "BaseModel: UUID id, created_at, updated_at on all models"
  - "TenantModel: Automatic restaurant FK for tenant-scoped models"
  - "TenantManager: Use for any model that should auto-filter by restaurant"
  - "Permission hierarchy: owner/manager for admin, cashier for POS, kitchen/driver for operations"

# Metrics
duration: 18min
completed: 2026-02-03
---

# Phase 1 Plan 2: Multi-Tenant Auth Summary

**Custom User model with phone-based JWT auth, Restaurant model for multi-tenancy, contextvars-based tenant isolation, and comprehensive role-based permissions**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-03T18:10:00Z
- **Completed:** 2026-02-03T18:28:00Z
- **Tasks:** 3
- **Files modified:** 20+

## Accomplishments

- Custom User model with phone as username and 5-level role system
- Restaurant model with Ivory Coast defaults (XOF, Africa/Abidjan)
- JWT tokens with custom claims: name, role, restaurant_id, permissions
- TenantMiddleware + TenantManager for automatic tenant isolation
- Role-based permission classes for endpoint protection
- Owner registration creates user + restaurant atomically with immediate login
- Staff invite restricted to owner/manager roles
- 42 comprehensive tests covering models, API, and multi-tenant isolation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create core app with multi-tenant infrastructure** - `194bdf7` (feat)
2. **Task 2: Create authentication app with User and Restaurant models** - `dac5bd7` (feat)
3. **Task 3: Create comprehensive tests** - `7999cea` (test)

## Files Created/Modified

### Core App
- `apps/api/apps/core/models.py` - BaseModel and TenantModel abstract bases
- `apps/api/apps/core/context.py` - Thread-local restaurant context using contextvars
- `apps/api/apps/core/managers.py` - TenantManager for auto-filtering queries
- `apps/api/apps/core/middleware.py` - TenantMiddleware extracts restaurant from user
- `apps/api/apps/core/permissions.py` - IsOwner, IsOwnerOrManager, IsCashier, IsSameRestaurant
- `apps/api/apps/core/pagination.py` - StandardPagination with configurable page size

### Authentication App
- `apps/api/apps/authentication/models.py` - User (phone-based) and Restaurant models
- `apps/api/apps/authentication/serializers.py` - JWT with custom claims, registration
- `apps/api/apps/authentication/views.py` - Login, register, logout, staff management
- `apps/api/apps/authentication/urls.py` - /api/v1/auth/ routes
- `apps/api/apps/authentication/admin.py` - Django admin configuration

### Tests
- `apps/api/apps/authentication/tests/factories.py` - Factory Boy factories
- `apps/api/apps/authentication/tests/conftest.py` - Pytest fixtures
- `apps/api/apps/authentication/tests/test_models.py` - Model unit tests
- `apps/api/apps/authentication/tests/test_auth_api.py` - API integration tests

### Configuration
- `apps/api/config/settings/base.py` - AUTH_USER_MODEL, middleware, JWT config
- `apps/api/config/settings/testing.py` - Enable migrations for custom User
- `apps/api/config/urls.py` - Include authentication URLs
- `apps/api/conftest.py` - Remove custom db_setup that broke migrations

## Decisions Made

1. **Phone as username** - Standard in Ivory Coast market; users more likely to remember phone than email
2. **UUID primary keys** - Better for distributed systems, no sequential ID guessing
3. **contextvars for tenant context** - Thread-safe and async-compatible, cleaner than thread-local
4. **Role hierarchy** - owner > manager > cashier > kitchen/driver maps to real restaurant operations
5. **XOF currency default** - West African CFA franc for Ivory Coast market

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Database migration conflict**
- **Found during:** Task 2 (Running migrations)
- **Issue:** Admin migrations already applied before custom User model
- **Fix:** Removed old SQLite database and re-ran migrations fresh
- **Verification:** Migrations applied successfully in correct order
- **Committed in:** dac5bd7 (Task 2 commit)

**2. [Rule 3 - Blocking] Test database not creating tables**
- **Found during:** Task 3 (Running tests)
- **Issue:** Custom `django_db_setup` fixture overriding pytest-django, tables not created
- **Fix:** Removed custom fixture from root conftest.py, enabled migrations in testing.py
- **Files modified:** conftest.py, config/settings/testing.py
- **Verification:** All 42 tests pass
- **Committed in:** 7999cea (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for migrations and tests to work. No scope creep.

## Issues Encountered

- **Paginated response in tests:** Staff list endpoint returns paginated response, tests needed to access `response.data["results"]` instead of `response.data` directly. Fixed by checking for pagination in test assertions.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for next phases:**
- Menu management (02-menu) can use TenantModel for menu items
- Orders (03-orders) can use TenantModel and permission classes
- All future apps can leverage authentication infrastructure

**No blockers.**

---
*Phase: 01-foundation*
*Completed: 2026-02-03*
