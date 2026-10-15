"""The preference groups the suite reads."""

import datetime
import decimal
import uuid

from django import forms

from object_preferences.registry import register
from tests.testapp.models import Project


@register(Project, name="display")
class DisplayForm(forms.Form):
    """How a project's pages look and behave."""

    theme = forms.ChoiceField(
        choices=[("light", "Light"), ("dark", "Dark")], initial="light"
    )
    page_size = forms.IntegerField(initial=25, min_value=5, max_value=100)
    show_archived = forms.BooleanField(required=False)


@register(Project, name="typed")
class TypedForm(forms.Form):
    """One preference for each type that does not survive being stored as JSON."""

    start_date = forms.DateField(initial=datetime.date(2026, 1, 1))
    reminder_time = forms.TimeField(initial=datetime.time(9, 30))
    budget = forms.DecimalField(initial=decimal.Decimal("10.50"))
    timeout = forms.DurationField(required=False)
    token = forms.UUIDField(
        initial=uuid.UUID("12345678-1234-5678-1234-567812345678"), required=False
    )
    tags = forms.MultipleChoiceField(choices=[("a", "A"), ("b", "B")], required=False)
