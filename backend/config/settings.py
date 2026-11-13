"""Django settings for CharterStack.

Every deploy-specific value comes from an environment variable so the same code
runs locally (SQLite, DEBUG on) and in production (PostgreSQL, DEBUG off).
See `.env.example` for the full list.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DEBUG", default=True)

# A fixed fallback key is only acceptable for local development.
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("SECRET_KEY must be set when DEBUG is off.")
    SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:5173")
# Render sets this to the service's public hostname; trust it automatically.
if RENDER_HOST := os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(RENDER_HOST)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Let WhiteNoise serve static files under runserver too, exactly as in production.
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "charters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serves Django's static files and the built React app (frontend/dist).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "charters.middleware.VisitorTimezoneMiddleware",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# DATABASE_URL, e.g. postgres://user:pass@host:5432/charterstack. Falls back to SQLite.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
# Server default. Per-visitor time zone comes from the X-Timezone header (docs/API.md).
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

# In production Django serves the built React app: WhiteNoise serves
# frontend/dist at the site root (index.html for "/"). In development Vite
# serves it on :5173 instead, so a missing dist folder is fine.
FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", BASE_DIR.parent / "frontend" / "dist"))
if FRONTEND_DIST.is_dir():
    WHITENOISE_ROOT = FRONTEND_DIST
    WHITENOISE_INDEX_FILE = True


def _immutable_file(path: str, url: str) -> bool:
    """Vite's hashed bundles (/assets/index-abc123.js) can be cached forever."""
    return url.startswith("/assets/") or (
        url.startswith(f"/{STATIC_URL}") and ".min." not in url and len(url.split(".")) > 2
    )


WHITENOISE_IMMUTABLE_FILE_TEST = _immutable_file

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Session cookie auth with CSRF protection (docs/API.md). Endpoints are private by
# default; public ones (health, demo-login) opt out explicitly.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # R01: 24-hour HH:MM everywhere in the API.
    "TIME_FORMAT": "%H:%M",
    # docs/DEMO_SANDBOX.md safeguards. Exceeding a rate returns 429.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "120/min",
        "demo_login": "5/hour",
    },
    # Proxies in front of Django, so throttles read the client IP from X-Forwarded-For.
    "NUM_PROXIES": int(os.environ["NUM_PROXIES"]) if os.environ.get("NUM_PROXIES") else None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CharterStack API",
    "DESCRIPTION": "Charter-bus dispatch board and booking API.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Swagger UI must be reachable without logging in.
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
}

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
    # The platform health check may call over plain HTTP inside the network.
    SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_CONTENT_TYPE_NOSNIFF = True

# Demo sandbox (docs/DEMO_SANDBOX.md). The session cookie lasts as long as the sandbox.
DEMO_SANDBOX_HOURS = 24
SESSION_COOKIE_AGE = DEMO_SANDBOX_HOURS * 60 * 60
DEMO_SERVER_NAME = os.environ.get("DEMO_SERVER_NAME", "demo-server")

# Sample and reference data (docs/DEMO_SANDBOX.md). Lives at the repo root, next to backend/.
SEED_FILE = Path(os.environ.get("SEED_FILE", BASE_DIR.parent / "seed" / "seed_demo.json"))
