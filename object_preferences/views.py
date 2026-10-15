"""The page where a person changes a record's preferences."""

from typing import Any

from django.contrib import messages
from django.forms import BaseForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView

from object_preferences.fields import RecordPreferences
from object_preferences.registry import registry


@method_decorator(csrf_protect, name="dispatch")
class PreferencesView(DetailView):
    """Show every preference group of a record's model and save them together.

    Route it with ``as_view(model=...)``. The view applies no access rule, so a
    host project composes Django's own mixins or decorators with it.

    Attributes:
        template_name: The template that renders the page.
        context_object_name: The name of the record in the template context.
        success_url: Where to send the person after saving. The page itself
            when ``None``.
        success_message: The message added after a save.
    """

    template_name = "object_preferences/preferences_form.html"
    context_object_name = "record"
    success_url: str | None = None
    success_message = _("The preferences were saved.")

    def get_preferences(self) -> RecordPreferences:
        """Return the preferences of the record the page is for.

        Returns:
            The record's preferences accessor.

        Raises:
            ImproperlyConfigured: If the record's model has no preferences field.
        """
        model = self.object._meta.model
        preferences: RecordPreferences = getattr(
            self.object, registry.get_field(model).attname
        )
        return preferences

    def get_forms(self, data: Any = None) -> dict[str, BaseForm]:
        """Build the form of every group, prefixed with the group's name.

        Args:
            data: Submitted data to bind the forms to. They are unbound when
                omitted.

        Returns:
            Each group's form by group name, in registration order.
        """
        preferences = self.get_preferences()
        return {
            name: preferences.get_form(name, data=data, prefix=name)
            for name in preferences
        }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the forms of the record's groups unless they were passed in."""
        if "forms" not in kwargs:
            kwargs["forms"] = self.get_forms()
        return super().get_context_data(**kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Validate every group's form, then save them all or none.

        Args:
            request: The request, whose POST data holds every group's values.
            *args: Positional arguments from the URL.
            **kwargs: Keyword arguments from the URL.

        Returns:
            A redirect when every group is valid, else the page with the errors.
        """
        self.object = self.get_object()
        forms = self.get_forms(data=request.POST)
        # A list, so that every form is validated and every error is shown.
        valid = [form.is_valid() for form in forms.values()]
        if all(valid):
            return self.forms_valid(forms)
        return self.forms_invalid(forms)

    def forms_valid(self, forms: dict[str, BaseForm]) -> HttpResponse:
        """Apply every group's form to the record, save once and redirect.

        Args:
            forms: Each group's valid form by group name.

        Returns:
            A redirect to the success URL.
        """
        preferences = self.get_preferences()
        for name, form in forms.items():
            preferences.apply(name, form)
        preferences.save()
        messages.success(self.request, self.success_message, fail_silently=True)
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms: dict[str, BaseForm]) -> HttpResponse:
        """Show the page again with the forms and their errors.

        Args:
            forms: Each group's bound form by group name.

        Returns:
            The rendered page.
        """
        return self.render_to_response(self.get_context_data(forms=forms))

    def get_success_url(self) -> str:
        """Send the person to ``success_url``, or back to this page.

        Returns:
            The URL to redirect to after a save.
        """
        if self.success_url:
            return str(self.success_url)
        return self.request.path
