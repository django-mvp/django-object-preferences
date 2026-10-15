"""Fixtures shared across the test suite."""

import pytest

from tests.factories import ProjectFactory
from tests.testapp.models import Project


@pytest.fixture
def project(db) -> Project:
    """Return a saved project."""
    return ProjectFactory()
