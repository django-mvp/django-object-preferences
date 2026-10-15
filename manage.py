#!/usr/bin/env python
"""Run Django's command line for the example project."""

import os
import sys


def main() -> None:
    """Run the command given on the command line."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
