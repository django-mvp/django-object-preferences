"""The model field that turns preferences on for a model."""

from collections.abc import Iterator, Mapping, Sequence
from types import MappingProxyType
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.query_utils import DeferredAttribute
from django.utils.translation import gettext_lazy as _

from object_preferences.registry import registry


class RecordPreferences(Mapping[str, Mapping[str, Any]]):
    """One record's preferences, as the record's attribute returns them.

    It maps each group name declared for the record's model to a read-only
    mapping of that group's values.

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

    def __getitem__(self, name: str) -> Mapping[str, Any]:
        """Return one group's values, read-only.

        Args:
            name: The group's name.

        Returns:
            Each of the group's preferences by name, stored or default.

        Raises:
            KeyError: If no group of that name is declared for the record's model.
        """
        group = registry.get_group(type(self.record), name)
        return MappingProxyType(group.read(self.stored.get(name, {})))

    def get_form(
        self, name: str, /, data: Mapping[str, Any] | None = None, **kwargs: Any
    ) -> forms.BaseForm:
        """Return one group's form, starting from the record's current values.

        Args:
            name: The group's name.
            data: Submitted data to bind the form to. The form is unbound when
                omitted.
            **kwargs: Further keyword arguments for the form. An ``initial``
                is laid over the record's current values.

        Returns:
            An instance of the group's form.

        Raises:
            KeyError: If no group of that name is declared for the record's model.
        """
        group = registry.get_group(type(self.record), name)
        initial = {**self[name], **kwargs.pop("initial", {})}
        return group.form_class(data=data, initial=initial, **kwargs)

    def apply(self, name: str, form: forms.BaseForm) -> None:
        """Replace one group's stored values with those of a submitted form.

        The record is changed in memory only. Other groups' stored values are
        left as they are, and so is every stored value of this group that the
        form does not declare.

        Args:
            name: The group's name.
            form: A bound form of the group's form class.

        Raises:
            KeyError: If no group of that name is declared for the record's model.
            TypeError: If the form is not an instance of the group's form class.
            ValidationError: If the form is not valid, with the form's errors.
        """
        group = registry.get_group(type(self.record), name)
        if not isinstance(form, group.form_class):
            raise TypeError(
                f"Expected a {group.form_class.__name__} for group {name!r}, "
                f"not a {type(form).__name__}."
            )
        if not form.is_valid():
            raise ValidationError(form.errors.as_data())
        stored = self.stored
        changed = dict(stored) if isinstance(stored, dict) else {}
        values = group.to_stored(form, self.field.encoder)
        if values:
            changed[name] = values
        else:
            changed.pop(name, None)
        setattr(self.record, self.field.attname, changed)

    def __iter__(self) -> Iterator[str]:
        """Iterate over the names of the groups declared for the record's model."""
        return iter(group.name for group in registry.get_groups(type(self.record)))

    def __len__(self) -> int:
        """Return how many groups are declared for the record's model."""
        return len(registry.get_groups(type(self.record)))


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
