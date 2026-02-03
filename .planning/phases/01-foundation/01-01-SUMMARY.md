---
phase: 01-foundation
plan: 01
subsystem: backend-foundation
tags: [django, rest-framework, jwt, pytest, ruff]

dependency-graph:
  requires: []
  provides: [django-project, settings-hierarchy, health-endpoint, test-infrastructure]
  affects: [01-02, 01-03, 02-01]

tech-stack:
  added: [Django 5.2.11, djangorestframework 3.16.1, djangorestframework-simplejwt 5.5.1, psycopg 3.3.2, django-environ 0.12.0, dj-database-url 2.3.0, django-cors-headers 4.9.0, argon2-cffi 23.1.0, whitenoise 6.11.0, gunicorn 22.0.0, redis 5.3.1, pytest 8.4.2, pytest-django 4.11.1, ruff 0.15.0, mypy 1.19.1]
  patterns: [monorepo, settings-hierarchy, env-based-config]

key-files:
  created:
    - pyproject.toml
    - apps/api/manage.py
    - apps/api/config/settings/base.py
    - apps/api/config/settings/development.py
    - apps/api/config/settings/production.py
    - apps/api/config/settings/testing.py
    - apps/api/config/urls.py
    - apps/api/config/wsgi.py
    - apps/api/config/asgi.py
    - apps/api/requirements/base.txt
    - apps/api/requirements/development.txt
    - apps/api/requirements/production.txt
    - apps/api/requirements/testing.txt
    - apps/api/pytest.ini
    - apps/api/conftest.py
    - apps/api/apps/core/tests/test_health.py
    - .gitignore
    - .env.example
  modified: []

decisions:
  - id: django-5.2-lts
    choice: Django 5.2.11 LTS
    rationale: Long-term support version with stability guarantees
  - id: argon2-password-hasher
    choice: Argon2 as primary password hasher
    rationale: Most secure modern password hashing algorithm
  - id: settings-hierarchy
    choice: Split settings (base/dev/prod/test)
    rationale: Clean separation of environment-specific config
  - id: jwt-auth
    choice: SimpleJWT with 15min access, 7day refresh, rotation
    rationale: Secure defaults with token rotation for refresh tokens

metrics:
  duration: 11 minutes
  completed: 2026-02-03
---

# Phase 01 Plan 01: Django Project Foundation Summary

**One-liner:** Django 5.2 LTS monorepo foundation with DRF, JWT auth, pytest, and ruff at apps/api/

## What Was Built

### Task 1: Monorepo Structure with Django Project Skeleton
- Created project structure at `apps/api/` following monorepo pattern
- Configured `pyproject.toml` with ruff and mypy settings (target Python 3.12)
- Implemented settings hierarchy: base, development, production, testing
- Set up Django REST Framework with JWT authentication (SimpleJWT)
- Configured security defaults: Argon2 hashing, CORS headers, WhiteNoise
- Added health check endpoint at `/health/` returning `{"status": "ok"}`
- Created `.gitignore` and `.env.example` with documented variables

### Task 2: Dependencies and Development Tooling
- Created requirements files split by environment (base/dev/prod/test)
- Configured pytest with Django settings for testing environment
- Added conftest.py with API client fixtures
- Fixed lint errors in base settings (unused import, line length)

### Task 3: Verification and Initial Tests
- Created core app structure at `apps/api/apps/core/`
- Added health endpoint test cases (2 tests passing)
- Verified Django check passes with no issues
- Verified Django migrations run successfully
- Verified pytest discovers and runs tests
- Verified ruff lint passes
- Verified dev server starts and serves health endpoint

## Key Configuration

### Settings Hierarchy
- **base.py**: Shared config (Django apps, middleware, database, REST framework, JWT)
- **development.py**: DEBUG=True, CORS allow all, console email backend
- **production.py**: DEBUG=False (hardcoded), SSL redirect, secure cookies, HSTS
- **testing.py**: In-memory SQLite, MD5 password hasher for speed

### Django REST Framework
- Default authentication: JWT (SimpleJWT)
- Default permission: IsAuthenticated
- Pagination: 20 items per page
- JSON-only renderer (browsable API in development)

### JWT Configuration
- Access token: 15 minutes
- Refresh token: 7 days
- Token rotation enabled
- Blacklist after rotation enabled

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Python not installed**
- **Found during:** Plan initialization
- **Issue:** Python was not found on the Windows system
- **Fix:** Installed Python 3.12.10 via winget
- **Tracked as:** Blocking issue resolution

**2. [Rule 1 - Bug] Lint errors in base.py**
- **Found during:** Task 2 verification
- **Issue:** Unused `os` import and line too long (91 > 88 chars)
- **Fix:** Removed unused import, split long string
- **Files modified:** apps/api/config/settings/base.py
- **Commit:** Included in Task 2 commit

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 038cfc9 | feat | Create monorepo structure with Django project skeleton |
| 3f0fb04 | feat | Configure dependencies and development tooling |
| f0146da | test | Add health endpoint tests and verify project setup |

## Verification Results

| Check | Status |
|-------|--------|
| Django check | Pass - 0 issues |
| pytest | Pass - 2/2 tests |
| ruff lint | Pass - all checks |
| Dev server | Pass - health endpoint returns {"status": "ok"} |
| Production settings | Pass - DEBUG=False verified |

## Next Phase Readiness

**Ready for:**
- Plan 01-02: Custom User Model
- Plan 01-03: API Infrastructure

**Prerequisites provided:**
- Working Django project with runnable manage.py
- Configured test infrastructure (pytest, fixtures)
- Linting setup (ruff with Django rules)
- Settings hierarchy for environment management
- Database configuration via environment variables
