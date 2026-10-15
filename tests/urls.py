"""The suite's urlconf, for any route a test needs."""

from django.urls import path

from object_preferences.views import PreferencesView
from tests.testapp.models import Document, Plain, Project

urlpatterns = [
    path(
        "plain/<int:pk>/preferences/",
        PreferencesView.as_view(model=Plain),
        name="plain-preferences",
    ),
    path(
        "projects/<int:pk>/preferences/",
        PreferencesView.as_view(model=Project),
        name="project-preferences",
    ),
    path(
        "projects/<int:pk>/preferences/elsewhere/",
        PreferencesView.as_view(model=Project, success_url="/done/"),
        name="project-preferences-elsewhere",
    ),
    path(
        "documents/<uuid:pk>/preferences/",
        PreferencesView.as_view(model=Document),
        name="document-preferences",
    ),
]
