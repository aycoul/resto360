"""
Django testing settings for RESTO360 project.

These settings are optimized for running tests quickly.
"""
from .base import *  # noqa: F401, F403

# Debug off for testing to match production behavior
DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use in-memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Note: Migrations are enabled in tests because we use a custom User model
# that requires migrations to create the schema correctly.

# Email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}

# CORS - Allow all for testing
CORS_ALLOW_ALL_ORIGINS = True
