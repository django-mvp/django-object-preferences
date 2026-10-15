"""PreferencesField and the accessor its descriptor returns."""

from django import forms
from django.apps import apps
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
