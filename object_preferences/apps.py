"""App configuration for django-object-preferences."""

from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import gettext_lazy as _


class ObjectPreferencesConfig(AppConfig):
    """What a project gets when it adds this package to INSTALLED_APPS.

    The label is set explicitly rather than left to Django's default, which is
    the last segment of the module path. Two installed apps whose paths end in
    the same word collide on that default, and the error names neither of them
    clearly.
    """

    name = "object_preferences"
    label = "object_preferences"
    verbose_name = _("Object Preferences")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Import each installed app's ``preferences`` module to register its groups."""
        autodiscover_modules("preferences")
