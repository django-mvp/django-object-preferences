"""Views the suite routes to try the preferences page under an access rule."""

from django.contrib.auth.mixins import UserPassesTestMixin

from object_preferences.views import PreferencesView


class OwnPreferencesView(UserPassesTestMixin, PreferencesView):
    """Admit only the person whose record the page is for."""

    def test_func(self) -> bool:
        """Admit the person only when the record is their own.

        Returns:
            Whether the signed-in person is the record the page is for.
        """
        return self.request.user == self.get_object()
