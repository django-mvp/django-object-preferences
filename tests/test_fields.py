"""PreferencesField and the accessor its descriptor returns."""

import pytest
from django import forms
from django.apps import apps
from django.core.management import call_command
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.graph import MigrationGraph
from django.db.migrations.state import ProjectState

from object_preferences.fields import PreferencesField
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
