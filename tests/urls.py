"""The suite's urlconf, for any route a test needs."""

from django.contrib.auth.decorators import login_required, permission_required
from django.urls import path

from object_preferences.views import PreferencesView
from tests.testapp.models import Document, Plain, Project, User
from tests.testapp.views import MyPreferencesView, OwnPreferencesView

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
    path(
        "projects/<int:pk>/preferences/signed-in/",
        login_required(PreferencesView.as_view(model=Project)),
        name="project-preferences-signed-in",
    ),
    path(
        "projects/<int:pk>/preferences/permitted/",
        login_required(
            permission_required("testapp.change_project", raise_exception=True)(
                PreferencesView.as_view(model=Project)
            )
        ),
        name="project-preferences-permitted",
    ),
    path(
        "projects/<int:pk>/preferences/public/",
        PreferencesView.as_view(
            model=Project, queryset=Project.objects.filter(name__startswith="Public")
        ),
        name="project-preferences-public",
    ),
    path(
        "users/<int:pk>/preferences/",
        OwnPreferencesView.as_view(model=User),
        name="user-preferences",
    ),
    path("preferences/", MyPreferencesView.as_view(), name="own-preferences"),
]
