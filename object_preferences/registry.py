"""Preference groups and the registry that holds them."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import models

if TYPE_CHECKING:
    from object_preferences.fields import PreferencesField

UNSUPPORTED_FIELDS = (
    forms.ModelChoiceField,
    forms.FileField,
    forms.MultiValueField,
)


def model_label(model: type[models.Model]) -> str:
    """Return a model's name as ``app_label.ModelName``.

    Args:
        model: The model to name.

    Returns:
        The label, as Django writes it in its own messages.
    """
    return f"{model._meta.app_label}.{model.__name__}"


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
                f"{model_label(model)} must have exactly one PreferencesField "
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
        self.get_field(model)
        if name in self.declarations.get(model, {}):
            raise ImproperlyConfigured(
                f"A preference group named {name!r} is already registered for "
                f"{model_label(model)}."
            )
        for field_name, field in form_class().fields.items():
            if isinstance(field, UNSUPPORTED_FIELDS):
                raise ImproperlyConfigured(
                    f"{form_class.__name__}.{field_name} is a "
                    f"{type(field).__name__}, which cannot be a preference in "
                    f"group {name!r} of {model_label(model)}."
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
                f"No preference group {name!r} is declared for {model_label(model)}."
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
