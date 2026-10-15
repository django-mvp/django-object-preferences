"""Factories for the test app's models."""

import factory

from tests.testapp.models import Document, Plain, Project, User


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


class UserFactory(factory.django.DjangoModelFactory):
    """Build a person who can sign in with the password ``password``."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"person{n}")
    email = factory.Sequence(lambda n: f"person{n}@example.com")
    password = factory.django.Password("password")


class PlainFactory(factory.django.DjangoModelFactory):
    """Build a record that carries no preferences."""

    class Meta:
        model = Plain

    name = factory.Sequence(lambda n: f"Plain {n}")
