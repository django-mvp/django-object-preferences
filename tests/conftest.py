"""Fixtures shared across the test suite."""

from collections.abc import Iterator

import pytest

from object_preferences.registry import registry
from tests.factories import DocumentFactory, ProjectFactory, UserFactory
from tests.testapp.models import Document, Project, User


@pytest.fixture
def project(db) -> Project:
    """Return a saved project."""
    return ProjectFactory()


@pytest.fixture
def user(db) -> User:
    """Return a saved person, who carries preferences."""
    return UserFactory()


@pytest.fixture
def preference_registry() -> Iterator:
    """Return the registry, putting its declarations back after the test."""
    saved = {model: dict(groups) for model, groups in registry.declarations.items()}
    yield registry
    registry.declarations = saved


@pytest.fixture
def document(db) -> Document:
    """Return a saved document, which carries a preferences field but no groups."""
    return DocumentFactory()
