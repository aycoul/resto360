"""
Django testing settings for RESTO360 project.

These settings are optimized for running tests quickly.
"""
import os

# Check if we should skip GIS apps before importing base settings
# This is needed on Windows where GDAL may not be installed
SKIP_GIS_APPS = os.environ.get("SKIP_GIS_APPS", "0") == "1"

if SKIP_GIS_APPS:
    # Import base settings but override INSTALLED_APPS
    import sys
    from pathlib import Path
    from datetime import timedelta

    import dj_database_url
    import environ

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    env = environ.Env(
        DEBUG=(bool, False),
        ALLOWED_HOSTS=(list, []),
        CORS_ALLOWED_ORIGINS=(list, []),
    )
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        environ.Env.read_env(str(env_file))

    SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")
    DEBUG = False
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

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
        "apps.locations",
        "apps.ai",
        "apps.reservations",
        "apps.reviews",
        "apps.crm",
        "apps.website",
        "apps.social",
        "apps.marketplace",
        "apps.financing",
        "apps.invoicing",
        "apps.forecasting",
        "apps.reorder",
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
        ],
    }

    SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
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
    ASGI_APPLICATION = "config.asgi.application"

    # Payment provider settings (empty for tests)
    WAVE_API_KEY = ""
    WAVE_WEBHOOK_SECRET = ""
    WAVE_API_URL = "https://api.wave.com/v1"
    ORANGE_CLIENT_ID = ""
    ORANGE_CLIENT_SECRET = ""
    ORANGE_MERCHANT_KEY = ""
    ORANGE_API_URL = "https://api.orange.com/orange-money-webpay/dev/v1"
    MTN_SUBSCRIPTION_KEY = ""
    MTN_USER_ID = ""
    MTN_API_SECRET = ""
    MTN_ENVIRONMENT = "sandbox"
    MTN_CALLBACK_URL = ""
    FLUTTERWAVE_SECRET_KEY = ""
    FLUTTERWAVE_PUBLIC_KEY = ""
    FLUTTERWAVE_WEBHOOK_SECRET = ""
    FLUTTERWAVE_API_URL = "https://api.flutterwave.com/v3"
    PAYSTACK_SECRET_KEY = ""
    PAYSTACK_PUBLIC_KEY = ""
    PAYSTACK_API_URL = "https://api.paystack.co"
    CINETPAY_API_KEY = ""
    CINETPAY_SITE_ID = ""
    CINETPAY_SECRET_KEY = ""
    CINETPAY_API_URL = "https://api-checkout.cinetpay.com/v2"
    # DigitalPaye
    DIGITALPAYE_API_KEY = ""
    DIGITALPAYE_API_SECRET = ""
    DIGITALPAYE_WEBHOOK_SECRET = ""
    DIGITALPAYE_API_URL = "https://api.digitalpaye.com/v1"
    DIGITALPAYE_ENVIRONMENT = "sandbox"
else:
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

# Use in-memory channel layer for testing
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Skip certain URL patterns when SKIP_GIS_APPS is enabled
SKIP_DELIVERY_URLS = SKIP_GIS_APPS if "SKIP_GIS_APPS" in dir() else os.environ.get("SKIP_GIS_APPS", "0") == "1"
