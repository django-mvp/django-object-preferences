"""The example project's pages."""

from django.urls import include, path

from example.views import MyPreferencesView, ProjectListView, ProjectPreferencesView

urlpatterns = [
    path("", ProjectListView.as_view(), name="project-list"),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "projects/<int:pk>/preferences/",
        ProjectPreferencesView.as_view(),
        name="project-preferences",
    ),
    path("preferences/", MyPreferencesView.as_view(), name="my-preferences"),
]
