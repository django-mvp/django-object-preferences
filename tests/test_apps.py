"""ObjectPreferencesConfig."""

from object_preferences.registry import registry
from tests.testapp.models import Project


class TestObjectPreferencesConfig:
    def test_groups_declared_in_installed_apps_are_found_at_startup(self) -> None:
        names = [group.name for group in registry.get_groups(Project)]

        assert names == ["display", "typed"]
