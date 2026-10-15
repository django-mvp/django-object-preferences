"""Fill the example project's database with three projects."""

from typing import Any

from django.core.management.base import BaseCommand

from example.models import Project


class Command(BaseCommand):
    """Recreate the example projects, so running it twice gives the same result."""

    help = "Delete and recreate the example projects."

    def handle(self, *args: Any, **options: Any) -> None:
        """Create a project on defaults, one with changes and one changed back."""
        Project.objects.all().delete()

        Project.objects.create(name="Left on defaults")

        changed = Project.objects.create(name="Changed from code")
        changed.preferences.change("display", theme="dark", page_size=50)
        changed.preferences.save()

        changed_back = Project.objects.create(name="Changed, then changed back")
        changed_back.preferences.change("display", theme="dark")
        changed_back.preferences.change("display", theme="light")
        changed_back.preferences.save()

        self.stdout.write(f"Created {Project.objects.count()} example projects.")
