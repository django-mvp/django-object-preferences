"""Views the suite routes to try the preferences page under an access rule."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from object_preferences.views import PreferencesView


class OwnPreferencesView(UserPassesTestMixin, PreferencesView):
    """Admit only the person whose record the page is for."""

    def test_func(self) -> bool:
        """Admit the person only when the record is their own.

        Returns:
            Whether the signed-in person is the record the page is for.
        """
        return self.request.user == self.get_object()


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
