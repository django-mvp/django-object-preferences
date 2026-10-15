"""Fixtures shared across the test suite."""

from collections.abc import Iterator

import pytest

from object_preferences.registry import registry
from tests.factories import ProjectFactory
from tests.testapp.models import Project


@pytest.fixture
def project(db) -> Project:
    """Return a saved project."""
    return ProjectFactory()


@pytest.fixture
def preference_registry() -> Iterator:
    """Return the registry, putting its declarations back after the test."""
    saved = {model: dict(groups) for model, groups in registry.declarations.items()}
    yield registry
    registry.declarations = saved
