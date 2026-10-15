"""Fill the example project's database with four projects and four people."""

from typing import Any

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

from example.models import Project, User


class Command(BaseCommand):
    """Recreate the example data, so running it twice gives the same result."""

    help = "Delete and recreate the example projects and the sign-in accounts."

    def handle(self, *args: Any, **options: Any) -> None:
        """Create the projects, then the accounts, which all use the password below."""
        self.create_projects()
        self.create_accounts()

    def create_projects(self) -> None:
        """Create projects on defaults, changed, changed back and with a stale value."""
        Project.objects.all().delete()

        Project.objects.create(name="Left on defaults")

        changed = Project.objects.create(name="Changed from code")
        changed.preferences.change("display", theme="dark", page_size=50)
        changed.preferences.save()

        changed_back = Project.objects.create(name="Changed, then changed back")
        changed_back.preferences.change("display", theme="dark")
        changed_back.preferences.change("display", theme="light")
        changed_back.preferences.save()

        stale = Project.objects.create(name="Stored before the choices changed")
        stale.preferences = {"display": {"theme": "sepia"}}
        stale.save()

        self.stdout.write(f"Created {Project.objects.count()} example projects.")

    def create_accounts(self) -> None:
        """Create the sign-in accounts, all with the password ``password``."""
        User.objects.all().delete()

        self.create_user("regular.user@example.com")

        regular_two = self.create_user("regular.user2@example.com")
        regular_two.preferences.change("notifications", digest="weekly")
        regular_two.preferences.save()

        staff = self.create_user("staff.user@example.com", is_staff=True)
        staff.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="example", codename="change_project"
            )
        )

        self.create_user("super.user@example.com", is_staff=True, is_superuser=True)

        self.stdout.write(f"Created {User.objects.count()} example accounts.")

    def create_user(self, email: str, **extra: Any) -> User:
        """Create one account whose username is the email's local part.

        Args:
            email: The address the person signs in with.
            **extra: Further fields, such as ``is_staff``.

        Returns:
            The saved account.
        """
        return User.objects.create_user(
            username=email.split("@")[0], email=email, password="password", **extra
        )
