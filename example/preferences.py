"""The preferences a project carries."""

from django import forms

from example.models import Project
from object_preferences.registry import register


@register(Project, name="display")
class DisplayPreferences(forms.Form):
    """How a project's pages look and behave."""

    theme = forms.ChoiceField(
        choices=[("light", "Light"), ("dark", "Dark")], initial="light"
    )
    page_size = forms.IntegerField(initial=25, min_value=5, max_value=100)
    show_archived = forms.BooleanField(required=False)
