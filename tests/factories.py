"""Factories for the test app's models."""

import factory

from tests.testapp.models import Project


class ProjectFactory(factory.django.DjangoModelFactory):
    """Build a project, which carries preferences."""

    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
