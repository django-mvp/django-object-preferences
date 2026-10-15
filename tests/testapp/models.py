"""Models the suite declares preferences on."""

import uuid

from django.contrib.auth.models import AbstractUser
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


class Document(models.Model):
    """A record whose primary key is set before it is ever saved."""

    id = models.UUIDField(
        verbose_name=_("id"),
        help_text=_("The document's identifier, set when it is created."),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        verbose_name=_("name"),
        help_text=_("What the document is called."),
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


class User(AbstractUser):
    """A person who signs in and carries preferences."""

    preferences = PreferencesField()


class ProjectProxy(Project):
    """A model that inherits from one with preferences declared."""

    class Meta:
        proxy = True
