# Phase 1: Foundation - Research

**Researched:** 2026-02-03
**Domain:** Django 5.0+ Multi-tenant SaaS with JWT Authentication
**Confidence:** HIGH

## Summary

Phase 1 establishes the core foundation for RESTO360: multi-tenant architecture, authentication, role-based access control, development environment, and CI/CD pipeline. The research confirms Django 5.0+ with Django REST Framework remains the standard choice for Python SaaS APIs, with djangorestframework-simplejwt as the established JWT library.

The recommended approach uses shared-database multi-tenancy with row-level isolation via `restaurant_id` foreign keys, combined with a custom TenantMiddleware and TenantManager pattern. This matches the architecture already documented in ARCHITECTURE.md and is the industry standard for modern SaaS applications (used by Slack, GitHub, Shopify).

For the development environment, Docker Compose with PostgreSQL 15+ and Redis 7+ provides production parity. GitHub Actions handles CI/CD with direct deployment to Render.com via deploy hooks or the render.yaml Blueprint specification.

**Primary recommendation:** Use djangorestframework-simplejwt for JWT auth, implement row-level tenant isolation with custom middleware/managers, and deploy via Render Blueprints (render.yaml).

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2 LTS | Web framework | Stable LTS, excellent ORM, built-in admin |
| djangorestframework | 3.15+ | REST API toolkit | Industry standard for Django APIs, excellent docs |
| djangorestframework-simplejwt | 5.3+ | JWT authentication | Jazzband maintained, active development, blacklist support |
| psycopg | 3.2+ | PostgreSQL adapter | Modern async-capable, replaces psycopg2 |
| django-environ | 0.11+ | Environment configuration | Django-specific, DATABASE_URL parsing |
| gunicorn | 22+ | WSGI server | Production standard, Render.com compatible |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dj-database-url | 2.2+ | Database URL parsing | Render.com provides DATABASE_URL |
| django-cors-headers | 4.3+ | CORS handling | Required for Next.js PWA frontend |
| argon2-cffi | 23+ | Password hashing | Modern, secure password hasher |
| whitenoise | 6.6+ | Static file serving | Production static files without nginx |
| pytest-django | 4.8+ | Testing framework | Better fixtures, cleaner than unittest |
| pytest-factoryboy | 2.7+ | Test data factories | Integrates factory_boy with pytest fixtures |
| factory-boy | 3.3+ | Test data generation | Better than JSON fixtures, handles relationships |
| ruff | 0.4+ | Linting & formatting | Fast, replaces flake8+isort+black |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| simplejwt | dj-rest-auth + simplejwt | More features (registration, social auth) but more complexity for API-only |
| django-environ | python-decouple | Framework-agnostic but lacks Django-specific helpers |
| psycopg[binary] | psycopg2-binary | psycopg3 is newer, async-ready; psycopg2 more battle-tested |
| row-level isolation | django-tenants (schema) | Schema isolation is overkill for single-region SaaS |

**Installation:**

```bash
# requirements/base.txt
Django>=5.2,<5.3
djangorestframework>=3.15,<4.0
djangorestframework-simplejwt>=5.3,<6.0
psycopg[binary]>=3.2,<4.0
django-environ>=0.11,<1.0
dj-database-url>=2.2,<3.0
django-cors-headers>=4.3,<5.0
argon2-cffi>=23.1,<24.0
whitenoise>=6.6,<7.0
gunicorn>=22.0,<23.0
redis>=5.0,<6.0

# requirements/development.txt
-r base.txt
pytest>=8.0,<9.0
pytest-django>=4.8,<5.0
pytest-factoryboy>=2.7,<3.0
factory-boy>=3.3,<4.0
pytest-cov>=4.1,<5.0
ruff>=0.4,<1.0
mypy>=1.10,<2.0
django-stubs>=5.0,<6.0
```

## Architecture Patterns

### Recommended Project Structure

```
apps/api/
├── config/                     # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py            # Shared settings
│   │   ├── development.py     # Local dev overrides
│   │   ├── staging.py         # Staging overrides
│   │   └── production.py      # Production overrides
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/                   # Shared utilities
│   │   ├── models.py          # BaseModel, TenantModel
│   │   ├── managers.py        # TenantManager
│   │   ├── middleware.py      # TenantMiddleware
│   │   ├── permissions.py     # Role-based permissions
│   │   └── pagination.py      # Standard pagination
│   └── authentication/         # Phase 1 focus
│       ├── models.py          # User, Restaurant, Role
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── tests/
├── manage.py
├── pytest.ini
├── conftest.py
└── requirements/
```

### Pattern 1: Multi-Tenant Row-Level Isolation

**What:** All tenant-scoped models include a `restaurant` foreign key. A custom manager filters queries automatically.

**When to use:** All models that contain tenant-specific data (users, orders, menu items, etc.)

**Example:**

```python
# Source: Django 5.2 docs + industry patterns
# apps/core/models.py
from django.db import models
from django.utils import timezone
import uuid

class BaseModel(models.Model):
    """Abstract base for all models with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(BaseModel):
    """Abstract base for tenant-scoped models."""
    restaurant = models.ForeignKey(
        'authentication.Restaurant',
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )

    class Meta:
        abstract = True

# apps/core/managers.py
from django.db import models
from .context import get_current_restaurant

class TenantManager(models.Manager):
    """Auto-filters queryset by current tenant."""
    def get_queryset(self):
        qs = super().get_queryset()
        restaurant = get_current_restaurant()
        if restaurant:
            return qs.filter(restaurant=restaurant)
        return qs

# apps/core/context.py
from contextvars import ContextVar
from typing import Optional

_current_restaurant: ContextVar[Optional['Restaurant']] = ContextVar(
    'current_restaurant', default=None
)

def get_current_restaurant():
    return _current_restaurant.get()

def set_current_restaurant(restaurant):
    _current_restaurant.set(restaurant)
```

### Pattern 2: TenantMiddleware for Request Context

**What:** Middleware extracts tenant from JWT and sets context for the request lifecycle.

**When to use:** Every authenticated request that needs tenant scoping.

**Example:**

```python
# Source: Industry best practices
# apps/core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from .context import set_current_restaurant

class TenantMiddleware(MiddlewareMixin):
    """Extract restaurant from JWT and set tenant context."""

    def process_request(self, request):
        # JWT authentication happens before this middleware
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'restaurant'):
                set_current_restaurant(request.user.restaurant)
        return None

    def process_response(self, request, response):
        set_current_restaurant(None)  # Clear context
        return response
```

### Pattern 3: Custom User Model with Phone Login

**What:** Custom User model using phone number as username (common in West Africa where email is less common).

**When to use:** RESTO360 targets Ivorian market where phone-based login is standard.

**Example:**

```python
# Source: Django 5.2 docs - Custom User Model
# apps/authentication/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.core.models import BaseModel

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Users must have a phone number')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    phone = models.CharField(max_length=20, unique=True)  # +225XXXXXXXXX
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=150)
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.CASCADE,
        related_name='staff',
        null=True, blank=True  # Null for superusers
    )
    role = models.CharField(max_length=20, choices=[
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('kitchen', 'Kitchen'),
        ('driver', 'Driver'),
    ])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='fr')

    objects = UserManager()
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name']
```

### Pattern 4: Role-Based Permissions

**What:** Custom DRF permission classes that check user roles.

**When to use:** Protecting API endpoints based on user role.

**Example:**

```python
# Source: DRF docs - Custom Permissions
# apps/core/permissions.py
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """Only restaurant owners can access."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'owner'
        )

class IsOwnerOrManager(permissions.BasePermission):
    """Owners and managers can access."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ('owner', 'manager')
        )

class IsSameRestaurant(permissions.BasePermission):
    """User can only access their own restaurant's data."""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'restaurant'):
            return obj.restaurant == request.user.restaurant
        return True

# Usage: Combine with bitwise operators
# permission_classes = [IsAuthenticated & (IsOwner | IsOwnerOrManager)]
```

### Anti-Patterns to Avoid

- **Missing restaurant filter:** Never query tenant models without filtering by restaurant. Use TenantManager as defense.
- **Hardcoded settings:** Never put secrets in settings.py. Always use environment variables via django-environ.
- **save() without update_fields:** In concurrent environments, always specify `update_fields` to avoid race conditions.
- **null=True on CharField:** Use empty string, not null, for "no data" on CharField/TextField.
- **Synchronous external calls:** Payment webhooks and notifications should be async (Celery tasks).

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT tokens | Custom token generation | djangorestframework-simplejwt | Handles refresh, blacklist, custom claims correctly |
| Password hashing | Custom hashing | Django's PASSWORD_HASHERS with Argon2 | Secure defaults, timing-attack resistant |
| CORS headers | Manual header manipulation | django-cors-headers | Handles preflight, credentials, origins |
| Database URL parsing | Manual connection string parsing | dj-database-url | Handles all edge cases, Render.com compatible |
| Test data | Manual object creation | factory_boy + pytest-factoryboy | Handles relationships, sequences, lazy attributes |
| Environment config | os.environ.get() everywhere | django-environ | Type casting, defaults, DATABASE_URL support |
| Rate limiting | Custom middleware | DRF's built-in throttling | Configurable, tested, cached |

**Key insight:** Django and DRF have solved most common problems. The goal is configuration, not creation.

## Common Pitfalls

### Pitfall 1: Database Connection Exhaustion

**What goes wrong:** PostgreSQL hits connection limit under load; requests queue and timeout.

**Why it happens:** Each Gunicorn worker opens multiple connections. Without pooling, connections multiply quickly.

**How to avoid:**
- Use PgBouncer in production (Render.com provides this)
- Set `CONN_MAX_AGE` in settings (300 seconds typical)
- Monitor connection counts

**Warning signs:** Random 500 errors under load, "too many connections" in logs.

### Pitfall 2: Missing Tenant Filter on Queries

**What goes wrong:** Data leaks between restaurants; one tenant sees another's orders.

**Why it happens:** Developer forgets to add `.filter(restaurant=...)` on a query.

**How to avoid:**
- Always use TenantManager on tenant models
- Add PostgreSQL Row-Level Security as defense-in-depth
- Write integration tests that verify tenant isolation

**Warning signs:** Test that creates data for Restaurant A can see it when querying as Restaurant B.

### Pitfall 3: JWT Token Not Refreshing

**What goes wrong:** Users get logged out unexpectedly when access token expires.

**Why it happens:** Frontend doesn't implement token refresh flow correctly.

**How to avoid:**
- Use 15-minute access tokens, 7-day refresh tokens
- Frontend must intercept 401 responses and call refresh endpoint
- Implement token blacklist for logout

**Warning signs:** "Token expired" errors in frontend console.

### Pitfall 4: Race Conditions with Model.save()

**What goes wrong:** Concurrent updates overwrite each other; data corruption.

**Why it happens:** Two processes read same object, modify different fields, save full object.

**How to avoid:**
- Always use `save(update_fields=['field1', 'field2'])`
- Use `F()` expressions for counter increments
- Use `select_for_update()` for critical sections

**Warning signs:** Inventory counts wrong, order totals incorrect.

### Pitfall 5: DEBUG=True in Production

**What goes wrong:** Stack traces exposed to users; security vulnerability.

**Why it happens:** Environment variable not set correctly on deploy.

**How to avoid:**
- Production settings should have `DEBUG = False` hardcoded
- Use separate settings files (development.py, production.py)
- CI should verify DEBUG is False in production settings

**Warning signs:** Detailed error pages in production.

### Pitfall 6: Missing Database Migrations on Deploy

**What goes wrong:** 500 errors because new columns/tables don't exist.

**Why it happens:** Deploy script doesn't run migrations before starting new code.

**How to avoid:**
- Render.com: Use release command in render.yaml
- Always run `migrate --noinput` before starting gunicorn
- Test migration rollback procedures

**Warning signs:** "relation does not exist" or "column does not exist" errors.

## Code Examples

Verified patterns from official sources:

### JWT Configuration (simplejwt)

```python
# Source: djangorestframework-simplejwt docs
# config/settings/base.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('SECRET_KEY'),

    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'TOKEN_OBTAIN_SERIALIZER': 'apps.authentication.serializers.CustomTokenObtainPairSerializer',
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
}
```

### Custom Token Serializer with Restaurant Claims

```python
# Source: simplejwt docs - Customizing Token Claims
# apps/authentication/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['name'] = user.name
        token['role'] = user.role
        if user.restaurant:
            token['restaurant_id'] = str(user.restaurant.id)
        token['permissions'] = user.get_permissions_list()

        return token
```

### Docker Compose for Development

```yaml
# Source: Industry patterns + Render compatibility
# docker/docker-compose.yml
version: '3.9'

services:
  api:
    build:
      context: ../apps/api
      dockerfile: ../docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
      - DATABASE_URL=postgres://resto360:resto360@db:5432/resto360
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=true
    volumes:
      - ../apps/api:/app
    depends_on:
      - db
      - redis
    command: python manage.py runserver 0.0.0.0:8000

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: resto360
      POSTGRES_USER: resto360
      POSTGRES_PASSWORD: resto360
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

### Render.yaml Blueprint

```yaml
# Source: Render.com docs
# render.yaml
databases:
  - name: resto360-db
    databaseName: resto360
    plan: starter  # Upgrade from free for persistence
    postgresMajorVersion: 15

services:
  - type: keyvalue
    name: resto360-redis
    plan: starter
    maxmemoryPolicy: allkeys-lru
    ipAllowList: []  # Only accessible from Render network

  - type: web
    name: resto360-api
    runtime: python
    plan: starter
    buildCommand: |
      pip install -r apps/api/requirements/production.txt
      python apps/api/manage.py collectstatic --noinput
    startCommand: gunicorn --chdir apps/api config.wsgi:application
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
      - key: PYTHON_VERSION
        value: "3.12"
      - key: DATABASE_URL
        fromDatabase:
          name: resto360-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: resto360-redis
          type: keyvalue
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_HOSTS
        value: resto360-api.onrender.com
    healthCheckPath: /health/
    autoDeploy: false  # Manual deploys for production

envVarGroups:
  - name: resto360-secrets
    envVars:
      - key: SENTRY_DSN
        sync: false
```

### GitHub Actions CI Pipeline

```yaml
# Source: GitHub Actions + Django best practices
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv pip install ruff
      - run: ruff check apps/api/
      - run: ruff format --check apps/api/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: resto360_test
          POSTGRES_USER: resto360
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r apps/api/requirements/testing.txt
      - run: pytest apps/api/ --cov=apps --cov-report=xml
        env:
          DATABASE_URL: postgres://resto360:postgres@localhost:5432/resto360_test
          REDIS_URL: redis://localhost:6379/0
          DJANGO_SETTINGS_MODULE: config.settings.testing

  deploy-staging:
    needs: [lint, test]
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - run: curl -X POST ${{ secrets.RENDER_STAGING_DEPLOY_HOOK }}
```

### pytest Configuration

```ini
# Source: pytest-django docs
# apps/api/pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
```

### Factory Boy Example

```python
# Source: pytest-factoryboy docs
# apps/authentication/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from apps.authentication.models import User, Restaurant

class RestaurantFactory(DjangoModelFactory):
    class Meta:
        model = Restaurant

    name = factory.Sequence(lambda n: f'Restaurant {n}')
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(' ', '-'))
    phone = factory.Sequence(lambda n: f'+22507{n:08d}')
    timezone = 'Africa/Abidjan'
    currency = 'XOF'

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    phone = factory.Sequence(lambda n: f'+22501{n:08d}')
    name = factory.Faker('name')
    role = 'cashier'
    restaurant = factory.SubFactory(RestaurantFactory)
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

# apps/authentication/tests/conftest.py
from pytest_factoryboy import register
from .factories import RestaurantFactory, UserFactory

register(RestaurantFactory)
register(UserFactory)
```

### Ruff Configuration

```toml
# Source: Ruff docs + cookiecutter-django
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 88
exclude = [
    "migrations",
    "__pycache__",
    ".venv",
]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "DJ",  # flake8-django
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "B904",  # Allow unchained exceptions (fine for Django 404)
]

[tool.ruff.lint.isort]
known-first-party = ["apps", "config"]
known-third-party = ["django", "rest_framework"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| psycopg2 | psycopg (v3) | 2023 | Async support, better typing |
| flake8 + isort + black | ruff | 2023 | 10-100x faster, single tool |
| django-rest-auth | dj-rest-auth | 2020 | Original unmaintained |
| django-rest-framework-jwt | simplejwt | 2019 | jpadilla's abandoned |
| requirements.txt only | pyproject.toml + uv | 2024 | Faster installs, lockfiles |
| Schema-based multi-tenancy | Row-level isolation | 2022+ | Simpler, better for SaaS |
| unittest | pytest | 2018+ | Better fixtures, less boilerplate |

**Deprecated/outdated:**
- `djangorestframework-jwt` (jpadilla): Abandoned, use `simplejwt` instead
- `django-rest-auth`: Unmaintained, use `dj-rest-auth` if needed
- `psycopg2-binary`: Still works but psycopg3 is future
- `python-decouple` for Django: Works but `django-environ` has better Django integration

## Open Questions

Things that couldn't be fully resolved:

1. **PostgreSQL Row-Level Security (RLS) vs Application-Only Isolation**
   - What we know: RLS provides database-level defense-in-depth
   - What's unclear: Performance impact, complexity for Django ORM
   - Recommendation: Start with application-level isolation (TenantManager), add RLS later if needed

2. **Phone Number Format Validation**
   - What we know: Cote d'Ivoire uses +225 with 10 digits
   - What's unclear: Need to support other West African countries?
   - Recommendation: Start with +225, use django-phonenumber-field if expanding

3. **Session vs Stateless JWT for Admin**
   - What we know: Django admin uses sessions by default
   - What's unclear: Should admin also be JWT?
   - Recommendation: Keep session auth for admin, JWT for API only

## Sources

### Primary (HIGH confidence)
- [Django 5.2 Documentation](https://docs.djangoproject.com/en/5.2/) - Custom user model, settings, middleware
- [Django REST Framework](https://www.django-rest-framework.org/) - ViewSets, routers, permissions, authentication
- [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/) - JWT configuration, custom claims, blacklist
- [Render.com Docs](https://render.com/docs/deploy-django) - render.yaml Blueprint, Django deployment

### Secondary (MEDIUM confidence)
- [Building a Multi-Tenant SaaS in Django: Complete 2026 Architecture](https://medium.com/django-journal/building-a-multi-tenant-saas-in-django-complete-2026-architecture-e956e9f5086a) - Row-level isolation patterns
- [Complete Guide: Using PostgreSQL RLS in Django for Enterprise SaaS](https://medium.com/@yogeshkrishnanseeniraj/complete-guide-using-postgresql-rls-row-level-security-in-django-for-enterprise-saas-28da70684372) - RLS integration
- [Dockerizing Django with Postgres, Gunicorn, and Nginx | TestDriven.io](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/) - Docker patterns
- [Automating Django Deployment to Render with GitHub Actions](https://medium.com/@timkenar/automating-django-deployment-to-render-with-github-actions-ci-cd-for-multi-tenant-apps-c6649f5b8082) - CI/CD for multi-tenant apps
- [Cookiecutter Django Documentation - Linters](https://cookiecutter-django.readthedocs.io/en/latest/4-guides/linters.html) - Ruff configuration

### Tertiary (LOW confidence - validate before using)
- [Django Mistakes That Broke My First Production App](https://medium.com/@djangowiki/things-i-stopped-doing-in-django-after-my-first-production-disaster-87e85ba5a50d) - Anecdotal pitfalls
- [pytest-factoryboy documentation](https://pytest-factoryboy.readthedocs.io/) - Factory patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Django/DRF ecosystem is well-documented, simplejwt is industry standard
- Architecture: HIGH - Row-level isolation is documented pattern, matches ARCHITECTURE.md
- Pitfalls: MEDIUM - Based on community sources, some anecdotal
- Docker/CI: HIGH - Official docs and verified patterns

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days - stable ecosystem)
