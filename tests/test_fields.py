"""PreferencesField and the accessor its descriptor returns."""

import datetime
import decimal
from types import MappingProxyType

import pytest
from django import forms
from django.apps import apps
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.management import call_command
from django.db import DatabaseError, transaction
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.graph import MigrationGraph
from django.db.migrations.state import ProjectState
from django.utils import timezone

from object_preferences.fields import PreferencesField
from object_preferences.registry import registry
from tests.factories import DocumentFactory, ProjectFactory
from tests.testapp.models import Document, Project, ProjectProxy


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


class NotesForm(forms.Form):
    notes = forms.JSONField(required=False)


class MomentForm(forms.Form):
    moment = forms.DateTimeField(required=False)


class TimedForm(forms.Form):
    moment = forms.DateTimeField(required=False)
    count = forms.IntegerField(initial=1)


class DayFirstForm(forms.Form):
    day = forms.DateField(required=False, input_formats=["%d/%m/%Y"])
    time = forms.TimeField(required=False, input_formats=["%H.%M"])
    moment = forms.DateTimeField(required=False, input_formats=["%d/%m/%Y %H.%M"])


class ConvertingForm(forms.Form):
    label = forms.CharField(initial="none")
    enabled = forms.BooleanField(required=False)


class NamedForm(forms.Form):
    name = forms.CharField(initial="unnamed")


class ConsistentForm(forms.Form):
    low = forms.IntegerField(initial=1)
    high = forms.IntegerField(initial=10)

    def clean(self):
        cleaned = super().clean()
        if cleaned["low"] > cleaned["high"]:
            raise forms.ValidationError("Low is above high.", code="inverted")
        return cleaned


class NarrowedDisplayForm(forms.Form):
    theme = forms.ChoiceField(
        choices=[("light", "Light"), ("sepia", "Sepia")], initial="light"
    )
    page_size = forms.IntegerField(initial=25, min_value=5, max_value=100)
    show_archived = forms.BooleanField(required=False)


class TestRecordPreferences:
    def test_a_new_record_stores_nothing(self) -> None:
        record = ProjectFactory.build()

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
        other = ProjectFactory.build()
        other.preferences = {"display": {"theme": "dark"}}

        project.preferences = other.preferences

        assert project.preferences.stored == {"display": {"theme": "dark"}}

    def test_saving_a_record_assigned_an_accessor_stores_the_dictionary(
        self, project
    ) -> None:
        other = ProjectFactory.build()
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

    def test_applied_values_read_back_typed_after_a_save_and_reload(
        self, project
    ) -> None:
        data = {
            "start_date": "2026-03-04",
            "reminder_time": "08:15",
            "budget": "12.75",
        }
        project.preferences.apply("typed", project.preferences.get_form("typed", data))
        project.save()

        typed = Project.objects.get(pk=project.pk).preferences["typed"]
        assert typed["start_date"] == datetime.date(2026, 3, 4)
        assert typed["reminder_time"] == datetime.time(8, 15)
        assert typed["budget"] == decimal.Decimal("12.75")

    def test_applying_stores_only_values_that_differ_from_their_default(
        self, project
    ) -> None:
        data = {"theme": "dark", "page_size": "25"}

        project.preferences.apply(
            "display", project.preferences.get_form("display", data)
        )

        assert project.preferences.stored == {"display": {"theme": "dark"}}

    def test_applying_a_default_removes_the_stored_value_and_the_group(
        self, project
    ) -> None:
        project.preferences = {"display": {"theme": "dark"}}
        data = {"theme": "light", "page_size": "25"}

        project.preferences.apply(
            "display", project.preferences.get_form("display", data)
        )

        assert project.preferences.stored == {}

    def test_a_default_that_changes_later_reaches_a_record_that_applied_it(
        self, project, preference_registry
    ) -> None:
        data = {"theme": "light", "page_size": "25"}
        project.preferences.apply(
            "display", project.preferences.get_form("display", data)
        )
        del registry.declarations[Project]["display"]
        registry.register(Project, "display", ChangedDisplayForm)

        assert project.preferences["display"]["theme"] == "dark"

    def test_an_invalid_form_raises_with_the_field_and_its_code(self, project) -> None:
        form = project.preferences.get_form(
            "display", {"theme": "dark", "page_size": "3"}
        )

        with pytest.raises(ValidationError) as raised:
            project.preferences.apply("display", form)

        assert [e.code for e in raised.value.error_dict["page_size"]] == ["min_value"]

    def test_an_invalid_form_leaves_the_stored_dictionary_unchanged(
        self, project
    ) -> None:
        project.preferences = {"display": {"page_size": 40}}
        form = project.preferences.get_form(
            "display", {"theme": "dark", "page_size": "3"}
        )

        with pytest.raises(ValidationError):
            project.preferences.apply("display", form)

        assert project.preferences.stored == {"display": {"page_size": 40}}

    def test_an_error_from_the_forms_own_clean_is_not_tied_to_a_field(
        self, project, preference_registry
    ) -> None:
        registry.register(Project, "range", ConsistentForm)
        form = project.preferences.get_form("range", {"low": "5", "high": "2"})

        with pytest.raises(ValidationError) as raised:
            project.preferences.apply("range", form)

        codes = [e.code for e in raised.value.error_dict[NON_FIELD_ERRORS]]
        assert codes == ["inverted"]

    def test_applying_an_unbound_form_is_a_value_error(self, project) -> None:
        form = project.preferences.get_form("display")

        with pytest.raises(ValueError, match="bound"):
            project.preferences.apply("display", form)

    def test_a_form_of_another_class_is_a_type_error(self, project) -> None:
        form = ChangedDisplayForm({"theme": "dark", "page_size": "50"})

        with pytest.raises(TypeError):
            project.preferences.apply("display", form)

    def test_applying_to_an_undeclared_group_is_a_key_error_naming_it(
        self, project
    ) -> None:
        form = project.preferences.get_form("display")

        with pytest.raises(KeyError, match="missing"):
            project.preferences.apply("missing", form)

    def test_applying_one_group_leaves_the_others_stored_values(self, project) -> None:
        project.preferences = {
            "typed": {"budget": "1.00"},
            "retired": {"colour": "red"},
        }
        data = {"theme": "dark", "page_size": "25"}

        project.preferences.apply(
            "display", project.preferences.get_form("display", data)
        )

        assert project.preferences.stored == {
            "typed": {"budget": "1.00"},
            "retired": {"colour": "red"},
            "display": {"theme": "dark"},
        }

    def test_applying_a_group_drops_a_stored_key_it_does_not_declare(
        self, project
    ) -> None:
        project.preferences = {"display": {"theme": "dark", "retired": 1}}
        data = {"theme": "dark", "page_size": "25"}

        project.preferences.apply(
            "display", project.preferences.get_form("display", data)
        )

        assert project.preferences.stored == {"display": {"theme": "dark"}}

    def test_applying_does_not_change_the_dictionary_it_replaces(self, project) -> None:
        before = project.preferences.stored
        data = {"theme": "dark", "page_size": "25"}

        project.preferences.apply(
            "display", project.preferences.get_form("display", data)
        )

        assert before == {}
        assert project.preferences.stored is not before

    def test_a_json_preference_set_to_a_string_survives_a_save_and_reload(
        self, project, preference_registry
    ) -> None:
        registry.register(Project, "notes", NotesForm)
        form = project.preferences.get_form("notes", {"notes": '"hello"'})

        project.preferences.apply("notes", form)
        project.save()

        reloaded = Project.objects.get(pk=project.pk)
        assert reloaded.preferences["notes"]["notes"] == "hello"

    def test_a_datetime_reads_as_the_instant_written_under_another_timezone(
        self, project, preference_registry
    ) -> None:
        registry.register(Project, "moments", MomentForm)
        written = datetime.datetime(2026, 3, 4, 12, 0, tzinfo=datetime.UTC)
        with timezone.override("Pacific/Auckland"):
            project.preferences.change("moments", moment=written)
            project.preferences.save()
        reloaded = Project.objects.get(pk=project.pk)

        with timezone.override("America/New_York"):
            assert reloaded.preferences["moments"]["moment"] == written

    def test_changing_a_sibling_keeps_a_datetime_stored_in_a_repeated_hour(
        self, project, preference_registry
    ) -> None:
        registry.register(Project, "timed", TimedForm)
        moment = datetime.datetime(2026, 11, 1, 6, 30, tzinfo=datetime.UTC)
        with timezone.override("UTC"):
            project.preferences.change("timed", moment=moment)

        with timezone.override("America/Chicago"):
            project.preferences.change("timed", count=5)

        assert project.preferences["timed"] == {"moment": moment, "count": 5}

    def test_changing_a_sibling_drops_a_stale_value_its_field_would_convert(
        self, project, preference_registry
    ) -> None:
        registry.register(Project, "converting", ConvertingForm)
        project.preferences = {"converting": {"label": ["a", "b"]}}

        project.preferences.change("converting", enabled=True)

        assert project.preferences.stored == {"converting": {"enabled": True}}

    def test_temporal_values_read_back_when_the_field_accepts_no_iso_format(
        self, project, preference_registry
    ) -> None:
        registry.register(Project, "dayfirst", DayFirstForm)
        written = {
            "day": datetime.date(2026, 3, 4),
            "time": datetime.time(7, 15),
            "moment": datetime.datetime(2026, 3, 4, 7, 15, tzinfo=datetime.UTC),
        }
        project.preferences.change("dayfirst", **written)
        project.preferences.save()

        reloaded = Project.objects.get(pk=project.pk)

        with timezone.override("UTC"):
            assert dict(reloaded.preferences["dayfirst"]) == written

    def test_changing_one_preference_keeps_the_groups_others(self, project) -> None:
        project.preferences = {"display": {"theme": "dark"}}

        project.preferences.change("display", page_size=50)

        assert project.preferences["display"] == {
            "theme": "dark",
            "page_size": 50,
            "show_archived": False,
        }
        assert project.preferences.stored == {
            "display": {"theme": "dark", "page_size": 50}
        }

    def test_changing_typed_preferences_stores_them_as_json(self, project) -> None:
        project.preferences.change("typed", budget=decimal.Decimal("3.25"))
        project.save()

        typed = Project.objects.get(pk=project.pk).preferences["typed"]
        assert typed["budget"] == decimal.Decimal("3.25")
        assert typed["start_date"] == datetime.date(2026, 1, 1)

    def test_changing_a_preference_back_to_its_default_stores_nothing(
        self, project
    ) -> None:
        project.preferences = {"display": {"theme": "dark"}}

        project.preferences.change("display", theme="light")

        assert project.preferences.stored == {}

    def test_changing_an_undeclared_preference_is_a_key_error_naming_it(
        self, project
    ) -> None:
        with pytest.raises(KeyError, match="missing"):
            project.preferences.change("display", theme="dark", missing=1)

    def test_a_failed_change_leaves_the_stored_dictionary_unchanged(
        self, project
    ) -> None:
        with pytest.raises(KeyError):
            project.preferences.change("display", theme="dark", missing=1)

        assert project.preferences.stored == {}

    def test_a_value_the_form_rejects_raises_and_changes_nothing(self, project) -> None:
        with pytest.raises(ValidationError) as raised:
            project.preferences.change("display", page_size=3)

        assert [e.code for e in raised.value.error_dict["page_size"]] == ["min_value"]
        assert project.preferences.stored == {}

    def test_changing_in_an_undeclared_group_is_a_key_error_naming_it(
        self, project
    ) -> None:
        with pytest.raises(KeyError, match="missing"):
            project.preferences.change("missing", theme="dark")

    def test_a_preference_called_name_can_be_changed(
        self, project, preference_registry
    ) -> None:
        registry.register(Project, "identity", NamedForm)

        project.preferences.change("identity", name="Atlas")

        assert project.preferences["identity"]["name"] == "Atlas"

    def test_a_saved_change_reads_back_after_a_reload(self, project) -> None:
        project.preferences.change("display", theme="dark")

        project.preferences.save()

        reloaded = Project.objects.get(pk=project.pk)
        assert reloaded.preferences["display"]["theme"] == "dark"

    def test_saving_writes_only_the_preferences(self, project) -> None:
        project.name = "Renamed"
        project.preferences.change("display", theme="dark")

        project.preferences.save()

        reloaded = Project.objects.get(pk=project.pk)
        assert reloaded.name != "Renamed"
        assert reloaded.preferences["display"]["theme"] == "dark"

    def test_saving_a_record_that_was_never_saved_raises_and_writes_nothing(
        self, db
    ) -> None:
        record = ProjectFactory.build()
        record.preferences.change("display", theme="dark")

        with transaction.atomic(), pytest.raises(ValueError):
            record.preferences.save()

        assert Project.objects.count() == 0

    def test_saving_a_record_with_a_default_key_that_was_never_saved_raises(
        self, db, preference_registry
    ) -> None:
        registry.register(Document, "moments", MomentForm)
        record = DocumentFactory.build()
        record.preferences.change("moments", moment=datetime.datetime(2026, 1, 1))

        with transaction.atomic(), pytest.raises(DatabaseError):
            record.preferences.save()

        assert Document.objects.count() == 0

    def test_a_stored_group_no_longer_declared_is_ignored(self, project) -> None:
        project.preferences = {"retired": {"theme": "dark"}, "display": {"x": 1}}

        assert project.preferences["display"]["page_size"] == 25
        assert "retired" not in project.preferences

    @pytest.mark.parametrize("stored", [None, [], "dark", 3])
    def test_a_stored_root_that_is_not_a_dictionary_reads_every_group_as_defaults(
        self, project, stored
    ) -> None:
        project.preferences = stored

        assert project.preferences["display"]["theme"] == "light"
        assert project.preferences["typed"]["budget"] == decimal.Decimal("10.50")

    @pytest.mark.parametrize("entry", [None, [], "dark", 3])
    def test_a_group_entry_that_is_not_a_dictionary_reads_as_defaults(
        self, project, entry
    ) -> None:
        project.preferences = {"display": entry}

        assert project.preferences["display"]["theme"] == "light"

    def test_a_stored_value_that_no_longer_fits_reads_the_default_beside_the_rest(
        self, project, preference_registry
    ) -> None:
        project.preferences = {"display": {"theme": "dark", "page_size": 40}}
        del preference_registry.declarations[Project]["display"]
        preference_registry.register(Project, "display", NarrowedDisplayForm)

        values = project.preferences["display"]

        assert values["theme"] == "light"
        assert values["page_size"] == 40

    def test_a_stale_stored_value_is_not_stored_after_the_group_is_changed(
        self, project, preference_registry
    ) -> None:
        project.preferences = {"display": {"theme": "dark", "page_size": 40}}
        project.preferences.save()
        del preference_registry.declarations[Project]["display"]
        preference_registry.register(Project, "display", NarrowedDisplayForm)

        project.preferences.change("display", page_size=60)
        project.preferences.save()

        reloaded = Project.objects.get(pk=project.pk)
        assert reloaded.preferences.stored == {"display": {"page_size": 60}}

    def test_a_model_inheriting_from_one_with_groups_has_none_of_them(
        self, project
    ) -> None:
        inheriting = ProjectProxy.objects.get(pk=project.pk)

        assert list(inheriting.preferences) == []
        with pytest.raises(KeyError, match="display"):
            inheriting.preferences["display"]
