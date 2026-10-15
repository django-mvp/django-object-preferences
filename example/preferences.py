"""The preferences a project and a person carry."""

from django import forms

from example.models import Project, User
from object_preferences.registry import register


@register(Project, name="display")
class DisplayPreferences(forms.Form):
    """How a project's pages look and behave."""

    theme = forms.ChoiceField(
        choices=[("light", "Light"), ("dark", "Dark")], initial="light"
    )
    page_size = forms.IntegerField(initial=25, min_value=5, max_value=100)
    show_archived = forms.BooleanField(required=False)


@register(User, name="display")
class PersonDisplayPreferences(forms.Form):
    """How the site looks to a person."""

    theme = forms.ChoiceField(
        choices=[("light", "Light"), ("dark", "Dark")], initial="light"
    )


@register(User, name="notifications")
class NotificationPreferences(forms.Form):
    """How a person is told about changes."""

    digest = forms.ChoiceField(
        choices=[("daily", "Daily"), ("weekly", "Weekly")], initial="daily"
    )
