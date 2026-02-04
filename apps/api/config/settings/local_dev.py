"""
Local development settings for RESTO360 project.

Uses SQLite file-based database and skips GIS apps for Windows compatibility.
"""
import os
from pathlib import Path
from datetime import timedelta

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize django-environ
env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

# Read .env file if it exists
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Installed apps without GIS
INSTALLED_APPS = [
    "daphne",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Skip: "django.contrib.gis",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "imagekit",
    # Skip: "rest_framework_gis",
    "simple_history",
    "apps.core",
    "apps.authentication",
    "apps.menu",
    "apps.orders",
    "apps.receipts",
    "apps.qr",
    "apps.inventory",
    "apps.payments",
    # Skip: "apps.delivery",
    "apps.analytics",
]

AUTH_USER_MODEL = "authentication.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Use file-based SQLite database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "TOKEN_OBTAIN_SERIALIZER": "apps.authentication.serializers.CustomTokenObtainPairSerializer",
}

CORS_ALLOW_ALL_ORIGINS = True

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# Channel layers - use in-memory for local dev
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Payment provider settings
WAVE_API_KEY = env("WAVE_API_KEY", default="")
WAVE_WEBHOOK_SECRET = env("WAVE_WEBHOOK_SECRET", default="")
WAVE_API_URL = env("WAVE_API_URL", default="https://api.wave.com/v1")
ORANGE_CLIENT_ID = env("ORANGE_CLIENT_ID", default="")
ORANGE_CLIENT_SECRET = env("ORANGE_CLIENT_SECRET", default="")
ORANGE_MERCHANT_KEY = env("ORANGE_MERCHANT_KEY", default="")
ORANGE_API_URL = env("ORANGE_API_URL", default="https://api.orange.com/orange-money-webpay/dev/v1")
MTN_SUBSCRIPTION_KEY = env("MTN_SUBSCRIPTION_KEY", default="")
MTN_USER_ID = env("MTN_USER_ID", default="")
MTN_API_SECRET = env("MTN_API_SECRET", default="")
MTN_ENVIRONMENT = env("MTN_ENVIRONMENT", default="sandbox")
MTN_CALLBACK_URL = env("MTN_CALLBACK_URL", default="")
FLUTTERWAVE_SECRET_KEY = env("FLUTTERWAVE_SECRET_KEY", default="")
FLUTTERWAVE_PUBLIC_KEY = env("FLUTTERWAVE_PUBLIC_KEY", default="")
FLUTTERWAVE_WEBHOOK_SECRET = env("FLUTTERWAVE_WEBHOOK_SECRET", default="")
FLUTTERWAVE_API_URL = env("FLUTTERWAVE_API_URL", default="https://api.flutterwave.com/v3")
PAYSTACK_SECRET_KEY = env("PAYSTACK_SECRET_KEY", default="")
PAYSTACK_PUBLIC_KEY = env("PAYSTACK_PUBLIC_KEY", default="")
PAYSTACK_API_URL = env("PAYSTACK_API_URL", default="https://api.paystack.co")
CINETPAY_API_KEY = env("CINETPAY_API_KEY", default="")
CINETPAY_SITE_ID = env("CINETPAY_SITE_ID", default="")
CINETPAY_SECRET_KEY = env("CINETPAY_SECRET_KEY", default="")
CINETPAY_API_URL = env("CINETPAY_API_URL", default="https://api-checkout.cinetpay.com/v2")

# DigitalPaye Configuration
DIGITALPAYE_API_KEY = env("DIGITALPAYE_API_KEY", default="")
DIGITALPAYE_API_SECRET = env("DIGITALPAYE_API_SECRET", default="")
DIGITALPAYE_WEBHOOK_SECRET = env("DIGITALPAYE_WEBHOOK_SECRET", default="")
DIGITALPAYE_API_URL = env("DIGITALPAYE_API_URL", default="https://api.digitalpaye.com/v1")
DIGITALPAYE_ENVIRONMENT = env("DIGITALPAYE_ENVIRONMENT", default="sandbox")

# Skip delivery URLs when GIS is not available
SKIP_DELIVERY_URLS = True

# Logging for development
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
}
