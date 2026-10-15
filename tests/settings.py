"""Django settings for testing django-object-preferences."""

SECRET_KEY = "django-insecure-test-key-for-object_preferences-tests-only"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "object_preferences",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    },
]

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
