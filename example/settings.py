"""Django settings for the example project."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# The example project only ever runs locally, so this key is not a secret.
SECRET_KEY = "django-insecure-example-project-runs-locally-only"

DEBUG = True

# The example project only ever runs locally, so any host may reach it.
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "object_preferences",
    "example",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

ROOT_URLCONF = "example.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    },
]

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
