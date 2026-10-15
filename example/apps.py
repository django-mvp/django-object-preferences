"""App configuration for the example project."""

from django.apps import AppConfig


class ExampleConfig(AppConfig):
    """The example app, which is also the example project."""

    name = "example"
    label = "example"
    default_auto_field = "django.db.models.BigAutoField"
