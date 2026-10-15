"""PreferencesView."""

import datetime

from django.urls import reverse

from tests.factories import ProjectFactory


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
