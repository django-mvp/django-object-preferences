"""The example project's views."""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView

from example.models import Project
from object_preferences.views import PreferencesView


class ProjectListView(ListView):
    """List the projects with the preferences each one reads."""

    model = Project


class ProjectPreferencesView(PermissionRequiredMixin, PreferencesView):
    """Let a person who may change projects change a project's preferences."""

    model = Project
    permission_required = "example.change_project"


class MyPreferencesView(LoginRequiredMixin, PreferencesView):
    """Show the signed-in person their own preferences."""

    def get_object(self, queryset=None):
        """Return the signed-in person as the record the page is for.

        Args:
            queryset: Unused, as the record is not looked up.

        Returns:
            The signed-in person.
        """
        return self.request.user
