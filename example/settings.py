"""Django settings for the example project."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# The example project only ever runs locally, so this key is not a secret.
SECRET_KEY = "django-insecure-example-project-runs-locally-only"

DEBUG = True

# The example project only ever runs locally, so any host may reach it.
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "object_preferences",
    "example",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

AUTH_USER_MODEL = "example.User"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "project-list"
LOGOUT_REDIRECT_URL = "project-list"

ROOT_URLCONF = "example.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
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

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
