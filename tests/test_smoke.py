"""The package installs into a Django project."""

from django.apps import apps


class TestPackagedApp:
    def test_app_is_installed(self) -> None:
        assert apps.is_installed("object_preferences")
