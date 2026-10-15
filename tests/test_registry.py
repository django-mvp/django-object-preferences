"""PreferenceRegistry and PreferenceGroup."""

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured

from object_preferences.fields import PreferencesField
from object_preferences.registry import PreferenceGroup, PreferenceRegistry
from object_preferences.registry import register as register_group
from object_preferences.registry import registry as default_registry
from tests.testapp.models import Plain, Project


class DisplayForm(forms.Form):
    theme = forms.ChoiceField(choices=[("light", "Light"), ("dark", "Dark")])


class ModelChoiceForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all())


class ModelMultipleChoiceForm(forms.Form):
    projects = forms.ModelMultipleChoiceField(queryset=Project.objects.all())


class FileForm(forms.Form):
    attachment = forms.FileField()


class ImageForm(forms.Form):
    picture = forms.ImageField()


class SplitDateTimeForm(forms.Form):
    starts = forms.SplitDateTimeField()


class LateModelChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["project"] = forms.ModelChoiceField(queryset=Project.objects.all())


class TestPreferenceRegistry:
    def test_a_registered_group_is_returned_by_name(self) -> None:
        registry = PreferenceRegistry()

        registry.register(Project, "display", DisplayForm)

        group = registry.get_group(Project, "display")
        assert (group.model, group.name, group.form_class) == (
            Project,
            "display",
            DisplayForm,
        )

    def test_register_returns_the_group(self) -> None:
        registry = PreferenceRegistry()

        group = registry.register(Project, "display", DisplayForm)

        assert isinstance(group, PreferenceGroup)
        assert registry.get_group(Project, "display") is group

    def test_get_groups_lists_groups_in_registration_order(self) -> None:
        registry = PreferenceRegistry()
        registry.register(Project, "display", DisplayForm)
        registry.register(Project, "other", DisplayForm)

        groups = registry.get_groups(Project)

        assert [group.name for group in groups] == ["display", "other"]

    def test_get_groups_of_a_model_with_none_is_empty(self) -> None:
        assert PreferenceRegistry().get_groups(Project) == []

    def test_the_decorator_registers_on_the_module_registry_and_returns_the_form(
        self, preference_registry
    ) -> None:
        decorated = register_group(Project, name="decorated")(DisplayForm)

        assert decorated is DisplayForm
        assert default_registry.get_group(Project, "decorated").form_class is (
            DisplayForm
        )

    def test_a_duplicate_name_on_one_model_is_refused(self) -> None:
        registry = PreferenceRegistry()
        registry.register(Project, "display", DisplayForm)

        with pytest.raises(ImproperlyConfigured):
            registry.register(Project, "display", DisplayForm)

    def test_a_model_without_the_field_is_refused(self) -> None:
        with pytest.raises(ImproperlyConfigured):
            PreferenceRegistry().register(Plain, "display", DisplayForm)

    @pytest.mark.parametrize(
        "form_class",
        [
            ModelChoiceForm,
            ModelMultipleChoiceForm,
            FileForm,
            ImageForm,
            SplitDateTimeForm,
            LateModelChoiceForm,
        ],
    )
    def test_a_form_with_an_unsupported_field_is_refused(self, form_class) -> None:
        with pytest.raises(ImproperlyConfigured):
            PreferenceRegistry().register(Project, "display", form_class)

    def test_a_refused_registration_leaves_nothing_registered(self) -> None:
        registry = PreferenceRegistry()

        with pytest.raises(ImproperlyConfigured):
            registry.register(Project, "display", FileForm)

        assert registry.get_groups(Project) == []

    def test_get_field_returns_the_field_of_a_model(self) -> None:
        field = PreferenceRegistry().get_field(Project)

        assert field is Project._meta.get_field("preferences")
        assert isinstance(field, PreferencesField)

    def test_get_field_refuses_a_model_without_the_field(self) -> None:
        with pytest.raises(ImproperlyConfigured):
            PreferenceRegistry().get_field(Plain)

    def test_an_undeclared_group_is_a_key_error_naming_it_and_the_model(self) -> None:
        with pytest.raises(KeyError) as excinfo:
            PreferenceRegistry().get_group(Project, "missing")

        assert "missing" in str(excinfo.value)
        assert "testapp.Project" in str(excinfo.value)
