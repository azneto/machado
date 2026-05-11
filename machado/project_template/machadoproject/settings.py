"""
Django settings for machadoproject.

All configuration is read from environment variables via a .env file.
See .env.example for the full list of available settings.
"""

import os
from pathlib import Path

import environ

# ── Base directory ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Environment ──────────────────────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
env.escape_proxy = True
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ── Core ─────────────────────────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ── Applications ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_yasg",
    "machado",
]


# ── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ── URLs ─────────────────────────────────────────────────────────────────────
ROOT_URLCONF = "machadoproject.urls"

# ── Templates ────────────────────────────────────────────────────────────────
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

# ── Database ─────────────────────────────────────────────────────────────────
DATABASES = {"default": env.db()}

# ── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True

# ── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = env("STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ── Default primary key ─────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── WSGI ─────────────────────────────────────────────────────────────────────
WSGI_APPLICATION = "machadoproject.wsgi.application"

# ── machado settings ─────────────────────────────────────────────────────────
MACHADO_VALID_TYPES = env.list(
    "MACHADO_VALID_TYPES", default=["gene", "mRNA", "polypeptide"]
)
MACHADO_OVERLAPPING_FEATURES = env.list(
    "MACHADO_OVERLAPPING_FEATURES", default=["SNV", "QTL", "copy_number_variation"]
)

if env("MACHADO_JBROWSE_URL", default=None):
    MACHADO_JBROWSE_URL = env("MACHADO_JBROWSE_URL")

if env("MACHADO_JBROWSE_OFFSET", default=None):
    MACHADO_JBROWSE_OFFSET = env.int("MACHADO_JBROWSE_OFFSET")

if env("MACHADO_JBROWSE_TRACKS", default=None):
    MACHADO_JBROWSE_TRACKS = env("MACHADO_JBROWSE_TRACKS")

# Optional API example settings — set only if defined in .env
_OPTIONAL_MACHADO_VARS = [
    "MACHADO_URL",
    "MACHADO_EXAMPLE_TXT",
    "MACHADO_EXAMPLE_ORGANISM_COMMON_NAME",
    "MACHADO_EXAMPLE_AA_ACC",
    "MACHADO_EXAMPLE_ORGANISM_ID",
    "MACHADO_EXAMPLE_AA",
    "MACHADO_EXAMPLE_NA",
]
for _var in _OPTIONAL_MACHADO_VARS:
    _val = env(_var, default=None)
    if _val is not None:
        globals()[_var] = _val
