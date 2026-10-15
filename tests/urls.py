"""The suite's urlconf, for any route a test needs."""

from django.urls import path

from object_preferences.views import PreferencesView
from tests.testapp.models import Document, Project

urlpatterns = [
    path(
        "projects/<int:pk>/preferences/",
        PreferencesView.as_view(model=Project),
        name="project-preferences",
    ),
    path(
        "documents/<uuid:pk>/preferences/",
        PreferencesView.as_view(model=Document),
        name="document-preferences",
    ),
]
