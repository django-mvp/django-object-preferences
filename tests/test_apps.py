"""ObjectPreferencesConfig."""

import pytest
from django.core.management import call_command

from object_preferences.registry import registry
from tests.testapp.models import Project
from tests.testapp.preferences import TypedForm


class TestObjectPreferencesConfig:
    def test_groups_declared_in_installed_apps_are_found_at_startup(self) -> None:
        names = [group.name for group in registry.get_groups(Project)]

        assert names == ["display", "typed"]

    def test_registering_and_replacing_a_group_leaves_no_migration_to_make(
        self, db, preference_registry
    ) -> None:
        del registry.declarations[Project]["display"]
        registry.register(Project, "display", TypedForm)

        try:
            call_command("makemigrations", check=True, dry_run=True)
        except SystemExit:
            pytest.fail("declaring preferences asked for a migration")
