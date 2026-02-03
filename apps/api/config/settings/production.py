"""
Django production settings for RESTO360 project.

These settings are for production deployment.
Security settings are enforced regardless of environment variables.
"""
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401, F403

# Sentry error tracking
SENTRY_DSN = env("SENTRY_DSN", default="")  # noqa: F405
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,  # 10% performance monitoring
        send_default_pii=False,  # GDPR compliance
        environment=env("ENVIRONMENT", default="production"),  # noqa: F405
    )

# SECURITY: Debug is always off in production
DEBUG = False

# Allowed hosts from environment
ALLOWED_HOSTS = env("ALLOWED_HOSTS")  # noqa: F405

# CORS - Only allow specific origins in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")  # noqa: F405

# Security settings for HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"

# BetterStack Logs
BETTERSTACK_SOURCE_TOKEN = env("BETTERSTACK_SOURCE_TOKEN", default="")  # noqa: F405

# Logging configuration for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
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
        "level": "WARNING",
    },
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Add BetterStack handler if token is configured
if BETTERSTACK_SOURCE_TOKEN:
    LOGGING["handlers"]["betterstack"] = {
        "class": "logtail.LogtailHandler",
        "source_token": BETTERSTACK_SOURCE_TOKEN,
    }
    LOGGING["root"]["handlers"].append("betterstack")
