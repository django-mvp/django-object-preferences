"""App configuration for the test app."""

from django.apps import AppConfig


class TestappConfig(AppConfig):
    """The test app that the suite installs next to the package."""

    name = "tests.testapp"
    label = "testapp"
    default_auto_field = "django.db.models.BigAutoField"
