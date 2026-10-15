"""Preference groups and the registry that holds them."""

import contextlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django import forms
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.utils.dateparse import parse_date, parse_datetime, parse_time

if TYPE_CHECKING:
    from object_preferences.fields import PreferencesField

UNSUPPORTED_FIELDS = (
    forms.ModelChoiceField,
    forms.FileField,
    forms.MultiValueField,
)

# The encoder stores these as ISO strings, which a field with its own
# input_formats may not accept, so they are parsed before the field cleans them.
TEMPORAL_PARSERS = (
    (forms.DateTimeField, parse_datetime),
    (forms.DateField, parse_date),
    (forms.TimeField, parse_time),
)


def dotted_path(form_class: type[forms.BaseForm]) -> str:
    """Return the importable dotted path of a form class.

    Args:
        form_class: The form class to name.

    Returns:
        The class's module and qualified name.
    """
    return f"{form_class.__module__}.{form_class.__qualname__}"


@dataclass(frozen=True)
class PreferenceGroup:
    """A named form, declared by one app for one model, whose fields are preferences.

    Attributes:
        model: The model whose records carry the group.
        name: The group's name, unique for the model.
        form_class: The form that declares the group's preferences.
    """

    model: type[models.Model]
    name: str
    form_class: type[forms.BaseForm]

    def defaults(self, form: forms.BaseForm | None = None) -> dict[str, Any]:
        """Return what each preference reads when nothing is stored for it.

        A preference's default is its field's initial value, or the value the
        field gives an empty submission when it has none. A required field with
        neither reads as empty rather than raising.

        Args:
            form: A form of the group to read the fields from. A fresh one is
                made when omitted.

        Returns:
            Each preference's default by name.
        """
        if form is None:
            form = self.form_class()
        defaults = {}
        for name, field in form.fields.items():
            value = form.get_initial_for_field(field, name)
            if value is None:
                value = field.widget.value_from_datadict({}, {}, name)
            try:
                defaults[name] = field.clean(value)
            except ValidationError:
                defaults[name] = field.to_python(value)
        return defaults

    def read(self, stored: Any) -> dict[str, Any]:
        """Return every preference of the group, typed as its field produces it.

        Args:
            stored: The values stored for this group. Anything but a dictionary
                reads as nothing stored, and a stored value the field no longer
                accepts reads as the default.

        Returns:
            Each preference's value by name, stored or default.
        """
        form = self.form_class()
        values = self.defaults(form)
        if not isinstance(stored, dict):
            return values
        for name, field in form.fields.items():
            if name in stored:
                # Stored data is untrusted and cleaning can raise more than
                # ValidationError, so no value may break a read (FR-016, SC-004).
                with contextlib.suppress(Exception):
                    value = stored[name]
                    for field_class, parser in TEMPORAL_PARSERS:
                        if isinstance(field, field_class) and isinstance(value, str):
                            value = parser(value) or value
                    values[name] = field.clean(value)
        return values

    def to_stored(
        self, form: forms.BaseForm, encoder: type[json.JSONEncoder] | None
    ) -> dict[str, Any]:
        """Return what a valid form of the group leaves stored on a record.

        Only values that differ from their default are kept, in the form the
        database returns them (the cleaned value, run through the encoder), so that the record reads the same before and
        after it is saved.

        Args:
            form: A valid form of the group.
            encoder: The JSON encoder of the record's preferences field.

        Returns:
            The values to store, by preference name.
        """
        defaults = self.defaults()
        stored = {}
        for name, field in form.fields.items():
            value = form.cleaned_data[name]
            if value != defaults[name]:
                # A JSONField value is kept as its JSON text, so a plain string
                # reads back as itself. Every other value goes through the encoder
                # whole, which keeps a datetime's offset.
                if isinstance(field, forms.JSONField):
                    value = field.prepare_value(value)
                stored[name] = json.loads(json.dumps(value, cls=encoder))
        return stored


class PreferenceRegistry:
    """The preference groups declared for each model.

    Attributes:
        declarations: Each model's groups by name, in registration order.
    """

    def __init__(self) -> None:
        """Start with nothing declared."""
        self.declarations: dict[type[models.Model], dict[str, PreferenceGroup]] = {}

    def get_field(self, model: type[models.Model]) -> "PreferencesField":
        """Return the one preferences field a model carries.

        Args:
            model: The model to look at.

        Returns:
            The model's ``PreferencesField``.

        Raises:
            ImproperlyConfigured: If the model has none, or more than one.
        """
        # fields.py imports this module, so the import cannot sit at the top.
        from object_preferences.fields import PreferencesField

        fields = [
            field
            for field in model._meta.get_fields()
            if isinstance(field, PreferencesField)
        ]
        if len(fields) != 1:
            raise ImproperlyConfigured(
                f"{model._meta.label} must have exactly one PreferencesField "
                f"to carry preferences, but has {len(fields)}."
            )
        return fields[0]

    def register(
        self, model: type[models.Model], name: str, form_class: type[forms.BaseForm]
    ) -> PreferenceGroup:
        """Declare a group of preferences for a model.

        Args:
            model: The model whose records carry the group.
            name: The group's name, unique for the model.
            form_class: The form whose fields are the group's preferences.

        Returns:
            The registered group.

        Raises:
            ImproperlyConfigured: If the model has no single preferences field,
                the name is taken, or the form has a field that refers to other
                records or carries an upload.
        """
        try:
            self.get_field(model)
        except ImproperlyConfigured as error:
            raise ImproperlyConfigured(
                f"Cannot register group {name!r} with {dotted_path(form_class)}: "
                f"{error}"
            ) from error
        taken = self.declarations.get(model, {}).get(name)
        if taken is not None:
            raise ImproperlyConfigured(
                f"A preference group named {name!r} is already registered for "
                f"{model._meta.label} with {dotted_path(taken.form_class)}, so "
                f"{dotted_path(form_class)} cannot be registered under it."
            )
        for field_name, field in form_class().fields.items():
            if isinstance(field, UNSUPPORTED_FIELDS):
                raise ImproperlyConfigured(
                    f"{form_class.__name__}.{field_name} is a "
                    f"{type(field).__name__}, which cannot be a preference in "
                    f"group {name!r} of {model._meta.label}."
                )
        group = PreferenceGroup(model, name, form_class)
        self.declarations.setdefault(model, {})[name] = group
        return group

    def get_groups(self, model: type[models.Model]) -> list[PreferenceGroup]:
        """List the groups declared for a model.

        Args:
            model: The model to list for. Parents and proxies are not included.

        Returns:
            The groups, in registration order.
        """
        return list(self.declarations.get(model, {}).values())

    def get_group(self, model: type[models.Model], name: str) -> PreferenceGroup:
        """Return one group declared for a model.

        Args:
            model: The model the group was declared for.
            name: The group's name.

        Returns:
            The group.

        Raises:
            KeyError: If no group of that name was declared for the model.
        """
        try:
            return self.declarations[model][name]
        except KeyError:
            raise KeyError(
                f"No preference group {name!r} is declared for {model._meta.label}."
            ) from None


registry = PreferenceRegistry()


def register(
    model: type[models.Model], *, name: str
) -> Callable[[type[forms.Form]], type[forms.Form]]:
    """Register the decorated form as a preference group of the module registry.

    Args:
        model: The model whose records carry the group.
        name: The group's name, unique for the model.

    Returns:
        A decorator that registers the form and returns it unchanged.
    """

    def decorator(form_class: type[forms.Form]) -> type[forms.Form]:
        """Register the form and hand it back."""
        registry.register(model, name, form_class)
        return form_class

    return decorator
