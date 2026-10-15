"""PreferencesField and the accessor its descriptor returns."""

import datetime
from types import MappingProxyType

import pytest
from django import forms
from django.apps import apps
from django.core.management import call_command
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.graph import MigrationGraph
from django.db.migrations.state import ProjectState

from object_preferences.fields import PreferencesField
from object_preferences.registry import registry
from tests.testapp.models import Project


def graph_with_testapp_migrated() -> MigrationGraph:
    """Return a graph that already has the test app's first migration."""
    graph = MigrationGraph()
    graph.add_node(("testapp", "0001_initial"), None)
    return graph


def project_state_without_preferences() -> ProjectState:
    """Return the app state with the preferences field taken off Project."""
    state = ProjectState.from_apps(apps)
    del state.models["testapp", "project"].fields["preferences"]
    return state


class TestPreferencesField:
    def test_adding_it_to_a_model_produces_one_add_field(self) -> None:
        autodetector = MigrationAutodetector(
            project_state_without_preferences(), ProjectState.from_apps(apps)
        )

        changes = autodetector.changes(
            graph=graph_with_testapp_migrated(), trim_to_apps={"testapp"}
        )

        operations = [op for m in changes["testapp"] for op in m.operations]
        assert len(changes["testapp"]) == 1
        assert [(type(op).__name__, op.model_name) for op in operations] == [
            ("AddField", "project")
        ]

    def test_the_test_app_migration_leaves_no_changes_to_make(self, db) -> None:
        try:
            call_command("makemigrations", "testapp", check=True, dry_run=True)
        except SystemExit:
            pytest.fail("makemigrations found changes the migration does not hold")

    def test_deconstruct_returns_no_keyword_arguments(self) -> None:
        _, _, _, kwargs = PreferencesField().deconstruct()

        assert kwargs == {}

    def test_deconstruct_keeps_a_value_the_host_overrides(self) -> None:
        _, _, _, kwargs = PreferencesField(blank=False).deconstruct()

        assert kwargs == {"blank": False}

    def test_it_has_a_verbose_name_and_help_text(self) -> None:
        field = Project._meta.get_field("preferences")

        assert field.verbose_name
        assert field.help_text

    def test_a_model_form_has_no_field_for_it(self) -> None:
        form_class = forms.modelform_factory(Project, fields="__all__")

        assert "preferences" not in form_class.base_fields


class ChangedDisplayForm(forms.Form):
    theme = forms.ChoiceField(
        choices=[("light", "Light"), ("dark", "Dark")], initial="dark"
    )
    page_size = forms.IntegerField(initial=50)
    show_archived = forms.BooleanField(required=False)


class TestRecordPreferences:
    def test_a_new_record_stores_nothing(self) -> None:
        record = Project(name="New")

        assert record.preferences.stored == {}

    def test_a_record_reloaded_from_the_database_stores_nothing(self, project) -> None:
        reloaded = Project.objects.get(pk=project.pk)

        assert reloaded.preferences.stored == {}

    def test_it_knows_its_record_and_its_field(self, project) -> None:
        accessor = project.preferences

        assert accessor.record is project
        assert accessor.field is Project._meta.get_field("preferences")

    def test_a_stored_dictionary_assigned_to_the_attribute_is_saved(
        self, project
    ) -> None:
        project.preferences = {"display": {"theme": "dark"}}
        project.save()

        reloaded = Project.objects.get(pk=project.pk)
        assert reloaded.preferences.stored == {"display": {"theme": "dark"}}

    def test_assigning_the_accessor_of_another_record_copies_its_stored_dictionary(
        self, project
    ) -> None:
        other = Project(name="Other")
        other.preferences = {"display": {"theme": "dark"}}

        project.preferences = other.preferences

        assert project.preferences.stored == {"display": {"theme": "dark"}}

    def test_saving_a_record_assigned_an_accessor_stores_the_dictionary(
        self, project
    ) -> None:
        other = Project(name="Other")
        other.preferences = {"display": {"theme": "dark"}}
        project.preferences = other.preferences
        project.save()

        reloaded = Project.objects.get(pk=project.pk)
        assert reloaded.preferences.stored == {"display": {"theme": "dark"}}

    def test_full_clean_passes_on_a_record(self, project) -> None:
        project.full_clean()

    def test_a_deferred_value_is_loaded_when_it_is_read(self, project) -> None:
        deferred = Project.objects.defer("preferences").get(pk=project.pk)

        assert deferred.preferences.stored == {}

    def test_the_field_reads_the_stored_dictionary_from_a_record(self, project) -> None:
        field = Project._meta.get_field("preferences")

        assert field.value_from_object(project) == {}

    def test_iterating_gives_the_names_of_the_declared_groups(self, project) -> None:
        assert list(project.preferences) == ["display", "typed"]

    def test_its_length_is_the_number_of_declared_groups(self, project) -> None:
        assert len(project.preferences) == 2

    def test_an_unchanged_preference_reads_its_default(self, project) -> None:
        assert project.preferences["display"]["theme"] == "light"

    def test_a_preference_with_no_initial_reads_the_empty_submission_value(
        self, project
    ) -> None:
        assert project.preferences["typed"]["timeout"] is None

    def test_a_stored_value_reads_back_as_the_field_type(self, project) -> None:
        project.preferences = {"typed": {"start_date": "2026-03-04"}}

        value = project.preferences["typed"]["start_date"]

        assert value == datetime.date(2026, 3, 4)

    def test_a_stored_value_survives_a_save_and_reload(self, project) -> None:
        project.preferences = {"display": {"page_size": 40}}
        project.save()

        reloaded = Project.objects.get(pk=project.pk)

        assert reloaded.preferences["display"]["page_size"] == 40

    def test_reading_every_preference_of_a_loaded_record_runs_no_queries(
        self, project, django_assert_num_queries
    ) -> None:
        loaded = Project.objects.get(pk=project.pk)

        with django_assert_num_queries(0):
            for group in loaded.preferences.values():
                list(group.values())

    def test_a_changed_default_reaches_a_record_with_nothing_stored(
        self, project, preference_registry
    ) -> None:
        del registry.declarations[Project]["display"]
        registry.register(Project, "display", ChangedDisplayForm)

        assert project.preferences["display"]["theme"] == "dark"

    def test_a_record_that_stored_its_own_value_keeps_reading_it(
        self, project, preference_registry
    ) -> None:
        project.preferences = {"display": {"theme": "light"}}
        del registry.declarations[Project]["display"]
        registry.register(Project, "display", ChangedDisplayForm)

        assert project.preferences["display"]["theme"] == "light"

    def test_an_undeclared_group_is_a_key_error_naming_it(self, project) -> None:
        with pytest.raises(KeyError, match="missing"):
            project.preferences["missing"]

    def test_an_undeclared_preference_is_a_key_error_naming_it(self, project) -> None:
        with pytest.raises(KeyError, match="missing"):
            project.preferences["display"]["missing"]

    def test_a_groups_values_are_read_only(self, project) -> None:
        values = project.preferences["display"]

        assert isinstance(values, MappingProxyType)
        with pytest.raises(TypeError):
            values["theme"] = "dark"

    def test_an_unbound_form_starts_from_the_records_current_values(
        self, project
    ) -> None:
        project.preferences = {"display": {"page_size": 40}}

        form = project.preferences.get_form("display")

        assert not form.is_bound
        assert form.initial == {
            "theme": "light",
            "page_size": 40,
            "show_archived": False,
        }

    def test_a_form_given_data_is_bound_and_validates_it(self, project) -> None:
        data = {"theme": "dark", "page_size": "3"}

        form = project.preferences.get_form("display", data=data)

        assert form.is_bound
        assert form.has_error("page_size", code="min_value")
        assert form.cleaned_data["theme"] == "dark"

    def test_an_initial_passed_in_wins_over_the_current_value(self, project) -> None:
        form = project.preferences.get_form("display", initial={"theme": "dark"})

        assert form.initial["theme"] == "dark"
        assert form.initial["page_size"] == 25

    def test_other_keyword_arguments_reach_the_form(self, project) -> None:
        form = project.preferences.get_form("display", prefix="display")

        assert form.prefix == "display"

    def test_a_form_for_an_undeclared_group_is_a_key_error_naming_it(
        self, project
    ) -> None:
        with pytest.raises(KeyError, match="missing"):
            project.preferences.get_form("missing")
