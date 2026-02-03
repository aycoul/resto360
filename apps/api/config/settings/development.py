"""
Django development settings for RESTO360 project.

These settings are only for local development.
"""
from .base import *  # noqa: F401, F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Use SQLite for development if DATABASE_URL not set
if "sqlite" in DATABASES["default"].get("ENGINE", ""):  # noqa: F405
    DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"  # noqa: F405

# Add browsable API renderer in development
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logging configuration for development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
