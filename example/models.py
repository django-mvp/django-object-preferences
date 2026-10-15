"""The example project's one model, which carries preferences."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from object_preferences.fields import PreferencesField


class Project(models.Model):
    """A project whose pages each person can set up their own way."""

    name = models.CharField(
        verbose_name=_("name"),
        help_text=_("What the project is called."),
        max_length=100,
    )
    preferences = PreferencesField()

    def __str__(self) -> str:
        """Return the project's name."""
        return self.name
