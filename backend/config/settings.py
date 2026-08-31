import os
import re
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import environ
from corsheaders.defaults import default_methods
from django.core.exceptions import ImproperlyConfigured

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# --- Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, "../.env"))
SECRET_KEY: str = env("SECRET_KEY")
DEBUG: bool = env("DEBUG")
ALLOWED_HOSTS: list[str] = env("ALLOWED_HOSTS").split(",")

DJANGO_APPS: tuple[str, ...] = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
)

THIRD_PARTY_APPS: tuple[str, ...] = (
    "unfold",  # muss vor django.contrib.admin laden
    "rest_framework",
    "daphne",
    "rest_framework.authtoken",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
)

LOCAL_APPS: tuple[str, ...] = ("apps.accounts", "apps.orders", "apps.core")
INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS

AUTH_USER_MODEL = "accounts.CustomUser"

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    }
}

UNFOLD = {
    "SITE_TITLE": "König 39 Solar & Elektro",
    "SITE_SYMBOL": "bolt",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": False,
    "THEME": "light",
    "BORDER_RADIUS": "6px",
    "COLORS": {
        # Sand (Sekundär) – frontend --color-sand-*
        "base": {
            "50": "#fafaf9",
            "100": "#f5f5f4",
            "200": "#e7e5e4",
            "300": "#d6d3d1",
            "400": "#a8a29e",
            "500": "#78716c",
            "600": "#57534e",
            "700": "#44403c",
            "800": "#292524",
            "900": "#1c1917",
            "950": "#0c0a09",
        },
        # Gold (Primär) – frontend --color-gold-*
        "primary": {
            "50": "#faf7f2",
            "100": "#f5ede0",
            "200": "#ead9c0",
            "300": "#dfc5a0",
            "400": "#d4a373",
            "500": "#c49363",
            "600": "#b38353",
            "700": "#8f6942",
            "800": "#6b4f32",
            "900": "#473521",
            "950": "#2a1f14",
        },
        # Textfarben – frontend body, nav, placeholders
        "font": {
            "subtle-light": "#78716c",
            "subtle-dark": "#a8a29e",
            "default-light": "#44403c",
            "default-dark": "#d6d3d1",
            "important-light": "#1c1917",
            "important-dark": "#f5f5f4",
        },
    },
}

CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = "/api/.*"

CORS_ALLOW_METHODS = default_methods

CORS_ALLOWED_ORIGINS: list[str] = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "apps.accounts.services.password_validator.EntirelyAlphabeticPasswordValidator",
    },
    {
        "NAME": "apps.accounts.services.password_validator.EntirelyNonCapitalLetterPasswordValidator",
    },
    {
        "NAME": "apps.accounts.services.password_validator.NoSmallLetterPasswordValidator",
    },
    {
        "NAME": "apps.accounts.services.password_validator.EntirelyNoneSpecialCharactersPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / env("DJANGO_STATIC_ROOT", default="staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / env("DJANGO_MEDIA_ROOT", default="media")

API_DOCS_ENABLED: bool = env.bool("API_DOCS_ENABLED", default=True)

FRONTEND_URL: str = env("FRONTEND_URL", default="http://localhost:3000")
# 1 Stunde statt Django-Default (3 Tage) - Passwort-Reset ist sicherheitskritisch,
# ein enges Zeitfenster reduziert das Risiko eines abgefangenen/weitergeleiteten
# Reset-Links (siehe ADR 0018).
PASSWORD_RESET_TIMEOUT = 3600
STRIPE_SECRET_KEY: str = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLIC_KEY: str = env("STRIPE_PUBLIC_KEY", default="")
STRIPE_WEBHOOK_SECRET: str = env("STRIPE_WEBHOOK_SECRET", default="")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 100,
    # --- To enable filtering, search and ordering in DRF ---------------- #
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Rate limiting setting that restricts access Telegram Login View.
    # It prevents a client from sending too many requests in a short period of time.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/hour",  # AnonRateThrottle (sign-up, checkout, …)
        "user": "1000/day",
        "contact": "5/hour",  # Spam protection for contact form submissions
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "König39 Shop API",
    "DESCRIPTION": "König39 Shop API Documentation",
    "VERSION": "0.0.0",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "VERIFYING_KEY": SECRET_KEY,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SIGNING_KEY": SECRET_KEY,
}
# --- Shop Config ----------------------------------- #
SHOP_NUMBER_PREFIX = env("SHOP_NUMBER_PREFIX")
CUSTOMER_NUMBER_KEY = env("CUSTOMER_NUMBER_KEY")
CUSTOMER_NUMBER_START = env.int("CUSTOMER_NUMBER_START", default=100001)

ORDER_NUMBER_KEY = env("ORDER_NUMBER_KEY")
ORDER_NUMBER_START = env.int("ORDER_NUMBER_START", default=1000)

TAX_RATE = Decimal(env("TAX_RATE"))
FREE_SHIPPING_THRESHOLD = Decimal(env("FREE_SHIPPING_THRESHOLD"))
SHIPPING_COST = Decimal(env("SHIPPING_COST"))
CURRENCY: str = env("CURRENCY", default="eur").strip().lower()  # sieh strip docs
if not re.fullmatch(r"[a-z]{3}", CURRENCY):
    raise ImproperlyConfigured(
        f"CURRENCY muss ein 3-stelliger ISO-4217-Code sein (z. B. 'eur'), "
        f"erhalten: {CURRENCY!r}"
    )

# --- Firmenstammdaten (Pflichtangaben Rechnung, §14 Abs. 4 UStG) ---- #
COMPANY_NAME = env("COMPANY_NAME")
COMPANY_STREET = env("COMPANY_STREET")
COMPANY_ZIP = env("COMPANY_ZIP")
COMPANY_CITY = env("COMPANY_CITY")
COMPANY_COUNTRY = env("COMPANY_COUNTRY", default="Deutschland")
COMPANY_TAX_ID = env("COMPANY_TAX_ID")  # Steuernummer oder USt-IdNr.

# --- Zusätzliche Pflichtangaben Impressum (§5 TMG, siehe ADR 0014) --- #
COMPANY_EMAIL = env("COMPANY_EMAIL")
COMPANY_PHONE = env("COMPANY_PHONE")
COMPANY_MANAGING_DIRECTOR = env("COMPANY_MANAGING_DIRECTOR", default="")
COMPANY_REGISTER_COURT = env("COMPANY_REGISTER_COURT", default="")
COMPANY_REGISTER_NUMBER = env("COMPANY_REGISTER_NUMBER", default="")

INVOICE_NUMBER_KEY = env("INVOICE_NUMBER_KEY", default="invoice_number")
INVOICE_NUMBER_START = env.int("INVOICE_NUMBER_START", default=1)

# --- Gutschriften/Korrekturrechnungen (siehe ADR 0016) --------------- #
CREDIT_NOTE_NUMBER_KEY = env("CREDIT_NOTE_NUMBER_KEY", default="credit_note_number")
CREDIT_NOTE_NUMBER_START = env.int("CREDIT_NOTE_NUMBER_START", default=1)

# --- E-Mail (Rechnungsversand, siehe ADR 0011) ----------------------- #
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# --- Celery (asynchroner Rechnungsversand, siehe ADR 0011) ---------- #
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/1")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple" if DEBUG else "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO" if DEBUG else "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# --- Produktions-Security (nur wirksam, wenn DEBUG=False) --------------- #
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=True)
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
