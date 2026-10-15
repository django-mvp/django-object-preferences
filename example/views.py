"""The example project's one view."""

from django.views.generic import ListView

from example.models import Project


class ProjectListView(ListView):
    """List the projects with the preferences each one reads."""

    model = Project
