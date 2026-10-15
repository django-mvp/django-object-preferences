"""Models the suite declares preferences on."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from object_preferences.fields import PreferencesField


class Project(models.Model):
    """A record that will carry preferences."""

    name = models.CharField(
        verbose_name=_("name"),
        help_text=_("What the project is called."),
        max_length=100,
    )
    preferences = PreferencesField()


class Plain(models.Model):
    """A record that carries no preferences."""

    name = models.CharField(
        verbose_name=_("name"),
        help_text=_("What the record is called."),
        max_length=100,
    )


class ProjectProxy(Project):
    """A model that inherits from one with preferences declared."""

    class Meta:
        proxy = True
