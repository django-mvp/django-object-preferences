"""The example project's one page."""

from django.urls import path

from example.views import ProjectListView

urlpatterns = [
    path("", ProjectListView.as_view(), name="project-list"),
]
