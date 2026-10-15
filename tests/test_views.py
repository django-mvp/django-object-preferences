"""PreferencesView."""

import datetime
import decimal

import pytest
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    ImproperlyConfigured,
    ValidationError,
)
from django.db.models.signals import post_save
from django.test import Client
from django.test.html import Element, parse_html
from django.urls import reverse

from object_preferences.registry import register
from tests.factories import PlainFactory, ProjectFactory, UserFactory
from tests.testapp.models import Project


def submission(**overrides: str) -> dict[str, str]:
    """Return the POST data of an unchanged Project page, with some values replaced."""
    data = {
        "display-theme": "light",
        "display-page_size": "25",
        "typed-start_date": "2026-01-01",
        "typed-reminder_time": "09:30:00",
        "typed-budget": "10.50",
        "typed-token": "12345678-1234-5678-1234-567812345678",
    }
    data.update(overrides)
    return data


def elements(node: Element | str, name: str) -> list[Element]:
    """Return every element called ``name`` in a parsed document."""
    if isinstance(node, str):
        return []
    found = [node] if node.name == name else []
    for child in node.children:
        found.extend(elements(child, name))
    return found


def attribute(node: Element, name: str) -> str | None:
    """Return an element's attribute, or None when it has none."""
    return dict(node.attributes).get(name)


def page(response) -> Element:
    """Parse a rendered page."""
    return parse_html(response.content.decode())


class TestPreferencesView:
    def test_the_page_has_a_form_for_every_group_with_a_control_for_every_preference(
        self, client, project
    ) -> None:
        response = client.get(reverse("project-preferences", args=[project.pk]))

        forms = response.context["forms"]
        assert response.status_code == 200
        assert list(forms) == ["display", "typed"]
        assert list(forms["display"].fields) == ["theme", "page_size", "show_archived"]
        assert list(forms["typed"].fields) == [
            "start_date",
            "reminder_time",
            "budget",
            "timeout",
            "token",
            "tags",
        ]
        assert not any(form.is_bound for form in forms.values())

    def test_a_preference_starts_from_its_stored_value_and_the_rest_from_defaults(
        self, client, db
    ) -> None:
        project = ProjectFactory(
            preferences={
                "display": {"theme": "dark"},
                "typed": {"start_date": "2026-03-04"},
            }
        )

        response = client.get(reverse("project-preferences", args=[project.pk]))

        forms = response.context["forms"]
        assert forms["display"].initial["theme"] == "dark"
        assert forms["display"].initial["page_size"] == 25
        assert forms["typed"].initial["start_date"] == datetime.date(2026, 3, 4)
        assert forms["typed"].initial["reminder_time"] == datetime.time(9, 30)

    def test_a_stored_value_that_no_longer_fits_starts_from_the_default(
        self, client, db
    ) -> None:
        project = ProjectFactory(preferences={"display": {"theme": "sepia"}})

        response = client.get(reverse("project-preferences", args=[project.pk]))

        assert response.status_code == 200
        assert response.context["forms"]["display"].initial["theme"] == "light"

    def test_the_controls_of_each_group_carry_the_groups_prefix(
        self, client, project
    ) -> None:
        response = client.get(reverse("project-preferences", args=[project.pk]))

        forms = response.context["forms"]
        assert forms["display"]["theme"].html_name == "display-theme"
        assert forms["typed"]["start_date"].html_name == "typed-start_date"

    def test_the_page_renders_with_the_packages_template(self, client, project) -> None:
        response = client.get(reverse("project-preferences", args=[project.pk]))

        assert "object_preferences/preferences_form.html" in [
            template.name for template in response.templates
        ]

    def test_the_record_is_in_the_context_as_record(self, client, project) -> None:
        response = client.get(reverse("project-preferences", args=[project.pk]))

        assert response.context["record"] == project

    def test_a_record_with_no_groups_opens_with_no_controls(
        self, client, document
    ) -> None:
        response = client.get(reverse("document-preferences", args=[document.pk]))

        assert response.status_code == 200
        assert response.context["forms"] == {}

    def test_a_record_that_does_not_exist_is_not_found(self, client, db) -> None:
        response = client.get(reverse("project-preferences", args=[999]))

        assert response.status_code == 404


class TestPreferencesViewWithoutPreferences:
    def test_a_model_with_no_preferences_fails_naming_the_model(
        self, client, db
    ) -> None:
        plain = PlainFactory()

        with pytest.raises(ImproperlyConfigured, match=r"testapp\.Plain"):
            client.get(reverse("plain-preferences", args=[plain.pk]))


class TestPreferencesViewSaving:
    def test_changes_in_two_groups_are_both_stored_and_the_page_is_shown_again(
        self, client, project
    ) -> None:
        url = reverse("project-preferences", args=[project.pk])
        data = submission(**{"display-theme": "dark", "typed-budget": "20.00"})

        response = client.post(url, data)

        project.refresh_from_db()
        assert response.status_code == 302
        assert response.url == url
        assert project.preferences["display"]["theme"] == "dark"
        assert project.preferences["typed"]["budget"] == decimal.Decimal("20.00")

    def test_an_invalid_group_stores_nothing_and_shows_both_entered_values(
        self, client, project
    ) -> None:
        url = reverse("project-preferences", args=[project.pk])
        data = submission(**{"display-page_size": "3", "typed-budget": "20.00"})

        response = client.post(url, data)

        project.refresh_from_db()
        forms_ = response.context["forms"]
        assert response.status_code == 200
        assert project.preferences.stored == {}
        assert forms_["display"].has_error("page_size", code="min_value")
        assert forms_["display"]["page_size"].value() == "3"
        assert forms_["typed"]["budget"].value() == "20.00"

    def test_an_error_from_a_forms_clean_is_the_groups_non_field_error(
        self, client, project, preference_registry
    ) -> None:
        @register(Project, name="strict")
        class StrictForm(forms.Form):
            flag = forms.BooleanField(required=False)

            def clean(self):
                raise ValidationError("Never valid.", code="never")

        url = reverse("project-preferences", args=[project.pk])

        response = client.post(url, submission())

        project.refresh_from_db()
        assert response.status_code == 200
        assert response.context["forms"]["strict"].has_error(
            NON_FIELD_ERRORS, code="never"
        )
        assert project.preferences.stored == {}

    def test_saving_an_unchanged_page_stores_nothing(self, client, project) -> None:
        response = client.post(
            reverse("project-preferences", args=[project.pk]), submission()
        )

        project.refresh_from_db()
        assert response.status_code == 302
        assert project.preferences.stored == {}

    def test_groups_with_a_preference_of_the_same_name_keep_their_own_values(
        self, client, project, preference_registry
    ) -> None:
        @register(Project, name="alerts")
        class AlertsForm(forms.Form):
            theme = forms.ChoiceField(
                choices=[("red", "Red"), ("blue", "Blue")], initial="red"
            )

        data = submission(**{"display-theme": "dark", "alerts-theme": "blue"})

        client.post(reverse("project-preferences", args=[project.pk]), data)

        project.refresh_from_db()
        assert project.preferences["display"]["theme"] == "dark"
        assert project.preferences["alerts"]["theme"] == "blue"

    def test_saving_adds_a_success_message(self, client, project) -> None:
        response = client.post(
            reverse("project-preferences", args=[project.pk]), submission()
        )

        levels = [m.level for m in messages.get_messages(response.wsgi_request)]
        assert levels == [messages.SUCCESS]

    def test_saving_works_without_the_messages_middleware(
        self, client, project, settings
    ) -> None:
        settings.MIDDLEWARE = [
            name for name in settings.MIDDLEWARE if "messages" not in name
        ]
        data = submission(**{"display-theme": "dark"})

        response = client.post(reverse("project-preferences", args=[project.pk]), data)

        project.refresh_from_db()
        assert response.status_code == 302
        assert project.preferences["display"]["theme"] == "dark"

    def test_success_url_is_where_the_person_is_sent(self, client, project) -> None:
        url = reverse("project-preferences-elsewhere", args=[project.pk])

        response = client.post(url, submission())

        assert response.status_code == 302
        assert response.url == "/done/"

    def test_saving_writes_the_preferences_and_nothing_else(
        self, client, project
    ) -> None:
        seen = []

        def receiver(sender, update_fields, **kwargs):
            seen.append(update_fields)

        post_save.connect(receiver, sender=Project)
        try:
            client.post(
                reverse("project-preferences", args=[project.pk]),
                submission(**{"display-theme": "dark"}),
            )
        finally:
            post_save.disconnect(receiver, sender=Project)

        assert seen == [frozenset({"preferences"})]

    def test_saving_a_record_with_no_groups_changes_nothing(
        self, client, document
    ) -> None:
        response = client.post(
            reverse("document-preferences", args=[document.pk]),
            {"display-theme": "dark"},
        )

        document.refresh_from_db()
        assert response.status_code == 302
        assert document.preferences.stored == {}

    def test_a_post_without_a_csrf_token_is_refused_even_with_no_csrf_middleware(
        self, project, settings
    ) -> None:
        settings.MIDDLEWARE = [
            name for name in settings.MIDDLEWARE if "csrf" not in name.lower()
        ]
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            reverse("project-preferences", args=[project.pk]),
            submission(**{"display-theme": "dark"}),
        )

        project.refresh_from_db()
        assert response.status_code == 403
        assert project.preferences.stored == {}


class TestPreferencesViewMarkup:
    def test_every_control_has_a_label_for_its_id(self, client, project) -> None:
        response = client.get(reverse("project-preferences", args=[project.pk]))

        document = page(response)
        controls = [
            control
            for tag in ("input", "select", "textarea")
            for control in elements(document, tag)
            if attribute(control, "type") != "hidden"
        ]
        labelled = {attribute(label, "for") for label in elements(document, "label")}
        assert controls
        assert all(attribute(control, "id") in labelled for control in controls)

    def test_each_group_is_a_fieldset_with_a_legend(self, client, project) -> None:
        response = client.get(reverse("project-preferences", args=[project.pk]))

        fieldsets = elements(page(response), "fieldset")
        assert len(fieldsets) == len(response.context["forms"])
        assert all(len(elements(fieldset, "legend")) == 1 for fieldset in fieldsets)

    def test_an_invalid_control_points_at_the_element_that_holds_its_error(
        self, client, project
    ) -> None:
        response = client.post(
            reverse("project-preferences", args=[project.pk]),
            submission(**{"display-page_size": "3"}),
        )

        document = page(response)
        control = next(
            control
            for control in elements(document, "input")
            if attribute(control, "name") == "display-page_size"
        )
        described_by = attribute(control, "aria-describedby").split()
        holders = [
            node
            for tag in ("div", "ul", "p", "span")
            for node in elements(document, tag)
            if attribute(node, "id") in described_by
        ]
        assert any(node.children for node in holders)


class TestPreferencesViewAccess:
    def test_an_anonymous_visitor_is_sent_to_sign_in_and_sees_no_form(
        self, client, project
    ) -> None:
        url = reverse("project-preferences-signed-in", args=[project.pk])

        response = client.get(url)

        assert response.status_code == 302
        assert response.url.startswith(f"{settings.LOGIN_URL}?next=")
        assert b"<form" not in response.content

    def test_a_signed_in_person_opens_and_saves_a_page_behind_login(
        self, client, project, user
    ) -> None:
        url = reverse("project-preferences-signed-in", args=[project.pk])
        client.force_login(user)

        opened = client.get(url)
        saved = client.post(url, submission(**{"display-theme": "dark"}))

        project.refresh_from_db()
        assert opened.status_code == 200
        assert saved.status_code == 302
        assert project.preferences["display"]["theme"] == "dark"

    def test_a_person_without_the_permission_is_refused_on_open_and_on_save(
        self, client, project, user
    ) -> None:
        url = reverse("project-preferences-permitted", args=[project.pk])
        client.force_login(user)

        opened = client.get(url)
        saved = client.post(url, submission(**{"display-theme": "dark"}))

        project.refresh_from_db()
        assert opened.status_code == 403
        assert saved.status_code == 403
        assert b"<form" not in opened.content
        assert project.preferences.stored == {}

    def test_a_person_with_the_permission_opens_and_saves(
        self, client, project, user
    ) -> None:
        url = reverse("project-preferences-permitted", args=[project.pk])
        user.user_permissions.add(Permission.objects.get(codename="change_project"))
        client.force_login(user)

        opened = client.get(url)
        saved = client.post(url, submission(**{"display-theme": "dark"}))

        project.refresh_from_db()
        assert opened.status_code == 200
        assert saved.status_code == 302
        assert project.preferences["display"]["theme"] == "dark"

    def test_a_record_outside_the_limited_queryset_is_not_found(
        self, client, db
    ) -> None:
        inside = ProjectFactory(name="Public plan")
        outside = ProjectFactory(name="Private plan")

        opened = client.get(reverse("project-preferences-public", args=[inside.pk]))
        refused = client.get(reverse("project-preferences-public", args=[outside.pk]))
        refused_save = client.post(
            reverse("project-preferences-public", args=[outside.pk]), submission()
        )

        assert opened.status_code == 200
        assert refused.status_code == 404
        assert refused_save.status_code == 404


class TestPreferencesViewRecordTest:
    def test_an_anonymous_visitor_is_sent_to_sign_in_and_sees_no_form(
        self, client, user
    ) -> None:
        response = client.get(reverse("user-preferences", args=[user.pk]))

        assert response.status_code == 302
        assert response.url.startswith(f"{settings.LOGIN_URL}?next=")
        assert b"<form" not in response.content

    def test_a_person_the_record_test_refuses_gets_403_on_open(
        self, client, user
    ) -> None:
        client.force_login(UserFactory())

        response = client.get(reverse("user-preferences", args=[user.pk]))

        assert response.status_code == 403
        assert b"<form" not in response.content

    def test_a_person_the_record_test_refuses_changes_nothing_by_posting(
        self, client, user
    ) -> None:
        client.force_login(UserFactory())

        response = client.post(
            reverse("user-preferences", args=[user.pk]),
            {"notifications-digest": "weekly"},
        )

        user.refresh_from_db()
        assert response.status_code == 403
        assert user.preferences.stored == {}

    def test_the_record_itself_opens_and_saves_its_page(self, client, user) -> None:
        url = reverse("user-preferences", args=[user.pk])
        client.force_login(user)

        opened = client.get(url)
        saved = client.post(url, {"notifications-digest": "weekly"})

        user.refresh_from_db()
        assert opened.status_code == 200
        assert saved.status_code == 302
        assert user.preferences["notifications"]["digest"] == "weekly"


class TestPreferencesViewForOwnPreferences:
    def test_a_signed_in_person_sees_their_own_stored_value(self, client, db) -> None:
        person = UserFactory(preferences={"notifications": {"digest": "weekly"}})
        UserFactory(preferences={"notifications": {"digest": "daily"}})
        client.force_login(person)

        response = client.get(reverse("own-preferences"))

        assert response.status_code == 200
        assert response.context["record"] == person
        assert response.context["forms"]["notifications"].initial["digest"] == "weekly"

    def test_saving_changes_their_own_record_and_not_another_persons(
        self, client, db
    ) -> None:
        person = UserFactory()
        other = UserFactory()
        client.force_login(person)

        response = client.post(
            reverse("own-preferences"), {"notifications-digest": "weekly"}
        )

        person.refresh_from_db()
        other.refresh_from_db()
        assert response.status_code == 302
        assert person.preferences["notifications"]["digest"] == "weekly"
        assert other.preferences.stored == {}

    def test_an_anonymous_visitor_is_sent_to_sign_in_and_sees_no_form(
        self, client, db
    ) -> None:
        response = client.get(reverse("own-preferences"))

        assert response.status_code == 302
        assert response.url.startswith(f"{settings.LOGIN_URL}?next=")
        assert b"<form" not in response.content
