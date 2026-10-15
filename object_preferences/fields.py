"""The model field that turns preferences on for a model."""

from collections.abc import Sequence
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.query_utils import DeferredAttribute
from django.utils.translation import gettext_lazy as _


class RecordPreferences:
    """One record's preferences, as the record's attribute returns them.

    Attributes:
        record: The record the preferences belong to.
        field: The field that stores them.
    """

    def __init__(self, record: models.Model, field: "PreferencesField") -> None:
        """Bind the accessor to a record and the field that stores its preferences.

        Args:
            record: The record the preferences belong to.
            field: The field that stores them.
        """
        self.record = record
        self.field = field

    @property
    def stored(self) -> Any:
        """The record's stored dictionary, as it is stored."""
        return self.record.__dict__[self.field.attname]


class PreferencesDescriptor(DeferredAttribute):
    """Return a record's preferences accessor instead of the raw stored value."""

    field: "PreferencesField"

    def __get__(self, instance: models.Model | None, cls: Any = None) -> Any:
        """Return the accessor for a record, or the descriptor on the class."""
        if instance is None:
            return self
        super().__get__(instance, cls)
        return RecordPreferences(instance, self.field)

    def __set__(self, instance: models.Model, value: Any) -> None:
        """Store a dictionary, or the stored dictionary of an accessor."""
        instance.__dict__[self.field.attname] = PreferencesField.unwrap(value)


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

    descriptor_class = PreferencesDescriptor

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

    @staticmethod
    def unwrap(value: Any) -> Any:
        """Return the stored dictionary when given an accessor, else the value.

        Args:
            value: A stored value or a ``RecordPreferences``.

        Returns:
            The value that is stored.
        """
        return value.stored if isinstance(value, RecordPreferences) else value

    def get_prep_value(self, value: Any) -> Any:
        """Unwrap an accessor before Django prepares the value for the database."""
        return super().get_prep_value(self.unwrap(value))

    def to_python(self, value: Any) -> Any:
        """Unwrap an accessor before Django converts the value."""
        return super().to_python(self.unwrap(value))

    def value_from_object(self, obj: models.Model) -> Any:
        """Return the stored dictionary rather than the accessor."""
        return self.unwrap(super().value_from_object(obj))
