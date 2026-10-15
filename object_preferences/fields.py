"""The model field that turns preferences on for a model."""

from collections.abc import Sequence
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _


class PreferencesField(models.JSONField):
    """The one field a model needs to carry preferences.

    It holds only the values a person has changed, as a dictionary of groups.
    A record with nothing changed stores an empty dictionary.
    """

    own_defaults: dict[str, Any] = {
        "default": dict,
        "blank": True,
        "editable": False,
        "encoder": DjangoJSONEncoder,
        "verbose_name": _("preferences"),
        "help_text": _("The preferences this record has changed from their defaults."),
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Apply this field's defaults to whatever the host did not set.

        Args:
            *args: Positional arguments for ``JSONField``.
            **kwargs: Keyword arguments for ``JSONField``, which win over the
                defaults.
        """
        for key, value in self.own_defaults.items():
            kwargs.setdefault(key, value)
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        """Leave out each keyword argument that still holds the field's own value."""
        name, path, args, kwargs = super().deconstruct()
        # Django omits these when they equal its own default, which differs from ours.
        for key in ("blank", "editable"):
            kwargs.setdefault(key, getattr(self, key))
        for key, value in self.own_defaults.items():
            if key in kwargs and kwargs[key] == value:
                del kwargs[key]
        return name, path, args, kwargs
