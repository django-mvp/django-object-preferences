"""Factories for the test app's models."""

import factory

from tests.testapp.models import Document, Project


class ProjectFactory(factory.django.DjangoModelFactory):
    """Build a project, which carries preferences."""

    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")


class DocumentFactory(factory.django.DjangoModelFactory):
    """Build a document, whose primary key is set before it is saved."""

    class Meta:
        model = Document

    name = factory.Sequence(lambda n: f"Document {n}")
