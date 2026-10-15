"""PreferenceRegistry and PreferenceGroup."""

import datetime
import decimal
import uuid

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder

from object_preferences.fields import PreferencesField
from object_preferences.registry import PreferenceGroup, PreferenceRegistry
from object_preferences.registry import register as register_group
from object_preferences.registry import registry as default_registry
from tests.testapp.models import Plain, Project
from tests.testapp.preferences import DisplayForm as ProjectDisplayForm
from tests.testapp.preferences import TypedForm


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

    def test_a_duplicate_name_error_names_the_model_the_name_and_both_forms(
        self,
    ) -> None:
        registry = PreferenceRegistry()
        registry.register(Project, "display", DisplayForm)

        with pytest.raises(ImproperlyConfigured) as excinfo:
            registry.register(Project, "display", ImageForm)

        message = str(excinfo.value)
        for expected in ("testapp.Project", "display", "DisplayForm", "ImageForm"):
            assert expected in message

    def test_a_model_without_the_field_error_names_the_model_group_and_form(
        self,
    ) -> None:
        with pytest.raises(ImproperlyConfigured) as excinfo:
            PreferenceRegistry().register(Plain, "display", DisplayForm)

        message = str(excinfo.value)
        for expected in ("testapp.Plain", "display", "DisplayForm"):
            assert expected in message

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


class RequiredForm(forms.Form):
    nickname = forms.CharField()
    count = forms.IntegerField()
    agreed = forms.BooleanField()
    colour = forms.ChoiceField(choices=[("red", "Red")])


class NarrowedDisplayForm(forms.Form):
    theme = forms.ChoiceField(choices=[("light", "Light"), ("sepia", "Sepia")])
    page_size = forms.IntegerField(initial=25, max_value=50)


class RetypedForm(forms.Form):
    page_size = forms.DateField(initial=datetime.date(2026, 1, 1))


class ConvertingForm(forms.Form):
    label = forms.CharField(initial="none")
    enabled = forms.BooleanField(required=False)


class OrderedForm(forms.Form):
    low = forms.IntegerField(initial=1)
    high = forms.IntegerField(initial=10)

    def clean(self):
        cleaned = super().clean()
        if cleaned["low"] > cleaned["high"]:
            raise forms.ValidationError("Low is above high.", code="inverted")
        return cleaned


class TestPreferenceGroup:
    def test_defaults_come_from_each_fields_initial_value(self) -> None:
        group = PreferenceGroup(Project, "display", ProjectDisplayForm)

        defaults = group.defaults()

        assert defaults["theme"] == "light"
        assert defaults["page_size"] == 25

    def test_a_field_with_no_initial_defaults_to_what_an_empty_submission_gives(
        self,
    ) -> None:
        group = PreferenceGroup(Project, "typed", TypedForm)

        defaults = group.defaults()

        assert defaults["timeout"] is None
        assert defaults["tags"] == []
        assert defaults["token"] == uuid.UUID("12345678-1234-5678-1234-567812345678")

    def test_an_unchecked_checkbox_defaults_to_false(self) -> None:
        group = PreferenceGroup(Project, "display", ProjectDisplayForm)

        assert group.defaults()["show_archived"] is False

    def test_a_required_field_with_no_initial_defaults_to_empty_without_raising(
        self,
    ) -> None:
        group = PreferenceGroup(Project, "required", RequiredForm)

        defaults = group.defaults()

        assert defaults == {
            "nickname": "",
            "count": None,
            "agreed": False,
            "colour": "",
        }

    def test_read_gives_the_default_for_a_preference_with_nothing_stored(self) -> None:
        group = PreferenceGroup(Project, "display", ProjectDisplayForm)

        values = group.read({"theme": "dark"}, DjangoJSONEncoder)

        assert values == {"theme": "dark", "page_size": 25, "show_archived": False}

    @pytest.mark.parametrize(
        ("name", "stored", "expected"),
        [
            ("start_date", "2026-03-04", datetime.date(2026, 3, 4)),
            ("reminder_time", "10:15:00", datetime.time(10, 15)),
            ("budget", "3.25", decimal.Decimal("3.25")),
            ("timeout", "P1DT02H00M00S", datetime.timedelta(days=1, hours=2)),
            (
                "token",
                "87654321-4321-8765-4321-876543218765",
                uuid.UUID("87654321-4321-8765-4321-876543218765"),
            ),
            ("tags", ["a", "b"], ["a", "b"]),
        ],
    )
    def test_a_stored_value_reads_as_the_type_its_field_produces(
        self, name, stored, expected
    ) -> None:
        group = PreferenceGroup(Project, "typed", TypedForm)

        value = group.read({name: stored}, DjangoJSONEncoder)[name]

        assert value == expected
        assert type(value) is type(expected)

    def test_a_stored_value_outside_narrowed_choices_reads_the_default(self) -> None:
        group = PreferenceGroup(Project, "display", NarrowedDisplayForm)

        values = group.read({"theme": "dark"}, DjangoJSONEncoder)

        assert values["theme"] == group.defaults()["theme"]

    def test_a_stored_value_above_a_lowered_maximum_reads_the_default(self) -> None:
        group = PreferenceGroup(Project, "display", NarrowedDisplayForm)

        values = group.read({"theme": "sepia", "page_size": 80}, DjangoJSONEncoder)

        assert values == {"theme": "sepia", "page_size": 25}

    def test_a_stored_value_of_a_changed_type_reads_the_default(self) -> None:
        group = PreferenceGroup(Project, "display", RetypedForm)

        values = group.read({"page_size": 25}, DjangoJSONEncoder)

        assert values == {"page_size": datetime.date(2026, 1, 1)}

    @pytest.mark.parametrize(
        ("name", "stored"), [("label", ["a", "b"]), ("enabled", "dark")]
    )
    def test_a_stored_value_its_field_would_convert_reads_the_default(
        self, name, stored
    ) -> None:
        group = PreferenceGroup(Project, "converting", ConvertingForm)

        value = group.read({name: stored}, DjangoJSONEncoder)[name]

        assert value == group.defaults()[name]

    def test_a_stored_value_whose_cleaning_raises_something_else_reads_the_default(
        self,
    ) -> None:
        group = PreferenceGroup(Project, "typed", TypedForm)

        values = group.read({"start_date": {"a": 1}}, DjangoJSONEncoder)

        assert values["start_date"] == datetime.date(2026, 1, 1)

    def test_a_stored_preference_no_longer_declared_is_ignored(self) -> None:
        group = PreferenceGroup(Project, "display", ProjectDisplayForm)

        values = group.read({"theme": "dark", "retired": 1}, DjangoJSONEncoder)

        assert values == {"theme": "dark", "page_size": 25, "show_archived": False}

    @pytest.mark.parametrize("stored", [None, [], "dark", 3, ["theme"]])
    def test_stored_values_that_are_not_a_dictionary_read_the_defaults(
        self, stored
    ) -> None:
        group = PreferenceGroup(Project, "display", ProjectDisplayForm)

        assert group.read(stored, DjangoJSONEncoder) == group.defaults()

    def test_a_stored_combination_the_form_now_rejects_still_reads_by_value(
        self,
    ) -> None:
        group = PreferenceGroup(Project, "ordered", OrderedForm)

        values = group.read({"low": 20, "high": 5}, DjangoJSONEncoder)

        assert values == {"low": 20, "high": 5}
