"""The example project's models, which carry preferences."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from object_preferences.fields import PreferencesField


class User(AbstractUser):
    """A person who signs in with their email address and has their own preferences."""

    email = models.EmailField(
        verbose_name=_("email address"),
        help_text=_("The address the person signs in with."),
        unique=True,
    )
    preferences = PreferencesField()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        """Return the person's email address."""
        return self.email


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
