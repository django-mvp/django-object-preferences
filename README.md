# django-object-preferences

[![Tests](https://github.com/django-mvp/django-object-preferences/actions/workflows/tests.yml/badge.svg)](https://github.com/django-mvp/django-object-preferences/actions/workflows/tests.yml)
[![Build](https://github.com/django-mvp/django-object-preferences/actions/workflows/build.yml/badge.svg)](https://github.com/django-mvp/django-object-preferences/actions/workflows/build.yml)
[![Publish](https://github.com/django-mvp/django-object-preferences/actions/workflows/publish.yml/badge.svg)](https://github.com/django-mvp/django-object-preferences/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/django-mvp/django-object-preferences/branch/main/graph/badge.svg)](https://codecov.io/gh/django-mvp/django-object-preferences)
[![PyPI](https://img.shields.io/pypi/v/django-object-preferences)](https://pypi.org/project/django-object-preferences/)
[![Python](https://img.shields.io/pypi/pyversions/django-object-preferences)](https://pypi.org/project/django-object-preferences/)
[![Django](https://img.shields.io/pypi/djversions/django-object-preferences)](https://pypi.org/project/django-object-preferences/)
[![License](https://img.shields.io/github/license/django-mvp/django-object-preferences)](https://github.com/django-mvp/django-object-preferences/blob/main/LICENSE)

Preferences stored on any Django model instance, declared with forms.

A person's theme, language and profile visibility, or how a project's or a
dataset's pages behave: settings like these belong to one record and are read
far more often than they are changed. This package keeps them in a single JSON
field on the record itself. Any installed app can declare its own group of
preferences without adding a model, a table or a migration.

> **Status:** early development. Nothing is published yet, and the first
> release will be 0.1.0.

## Scope & philosophy

django-object-preferences stores small, per-record settings and gives people a
page to change them. A record can be any model: the user model, or something
like a project or a dataset. Each app declares the preferences it needs with
an ordinary Django form, which already says what type each value is, how it is
validated, what its choices are and what it defaults to. Reading a preference
costs no extra query, because the values travel with the record.

What it deliberately is not:

- **A home for data the server selects records by.** A value the project filters
  or orders on belongs in a real column with an index. Whether a profile is
  public is the usual example. Preferences are read from a record already in
  hand.
- **Site-wide settings.** Values that apply to the whole site belong in Django
  settings or in a package built for that, such as django-constance.
- **A place for anything that sits between two records.** A person's choice
  about one particular project relates two records, and needs a model of its own.
- **A user interface framework.** The page it ships is plain Django template
  markup, which a project or a UI package restyles.

When two designs conflict, the one an experienced Django developer would
recognise wins over the cleverer one. Forms, model fields and class-based views
are used the way Django intends, and nothing is added that a project could do
just as well with what Django already provides.

## Installation

```bash
pip install django-object-preferences
```

Then add it to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "object_preferences",
]
```

## Usage

### Turning preferences on for a model

Add a `PreferencesField` to the model whose records should carry preferences,
then make and run the migration:

```python
from django.db import models

from object_preferences.fields import PreferencesField


class Project(models.Model):
    name = models.CharField(max_length=100)
    preferences = PreferencesField()
```

The field takes no arguments. It is one JSON column, and a model needs only
one. Its migration reads `PreferencesField()`, and it is the only migration
this package ever asks of your project: declaring preferences later adds no
table and no migration.

Reading `project.preferences` returns a `RecordPreferences`, which belongs to
that one record and is installed by the field's `PreferencesDescriptor`. It
knows its `record` and its `field`, and its `stored` property is the
dictionary the record keeps. A new record stores an empty dictionary, because
a record holds only the values someone has changed from their defaults:

```python
project = Project(name="Atlas")
project.preferences.stored  # {}
```

The field is not editable, so a `ModelForm` for the model leaves it out.

### Declaring a group of preferences

A group of preferences is an ordinary Django form, and each of its fields is
one preference. Register it for the model the way you would register a model
admin, in a module called `preferences.py` inside any installed app. The
package imports that module for every installed app when Django starts, so the
project's settings never list it:

```python
# projects/preferences.py
from django import forms

from object_preferences.registry import register

from .models import Project


@register(Project, name="display")
class DisplayPreferences(forms.Form):
    theme = forms.ChoiceField(
        choices=[("light", "Light"), ("dark", "Dark")], initial="light"
    )
    page_size = forms.IntegerField(initial=25, min_value=5, max_value=100)
    show_archived = forms.BooleanField(required=False)
```

`register` is the decorator form of `registry.register(model, name, form_class)`,
where `registry` is the project-wide `PreferenceRegistry`. A group's name is
unique for its model. Registering returns a `PreferenceGroup`, which knows its
`model`, its `name` and its `form_class`.

Startup stops with an `ImproperlyConfigured` error that names the problem when
two groups for one model share a name, when the model has no `PreferencesField`,
or when the form has a field that refers to other records or carries an upload
(`ModelChoiceField`, `FileField` and `MultiValueField`, with their subclasses).

To look groups up, ask the registry:

```python
from object_preferences.registry import registry

registry.get_groups(Project)           # every PreferenceGroup, in registration order
registry.get_group(Project, "display")  # one group, or a KeyError naming it
registry.get_field(Project)             # the model's PreferencesField
```

Groups belong to exactly the model they were registered for. A subclass or a
proxy of that model does not inherit them.

### Reading preferences

`project.preferences` maps each group's name to a read-only mapping of that
group's values:

```python
project.preferences["display"]["theme"]      # "light"
project.preferences["display"]["page_size"]  # 25
list(project.preferences)                    # ["display"]
```

Reading never queries the database, however many preferences it reads, because
the values travel with the record. Asking for a group or a preference that was
never declared raises a `KeyError` that names it.

A preference nobody has changed reads its default, and the default comes from
the field. It is the field's `initial` value. A field with no `initial` reads
the value an empty submission of the form would give it, so a `BooleanField`
reads `False`, an optional `DurationField` reads `None` and an optional
`MultipleChoiceField` reads an empty list. A required field with no `initial`
reads as empty: an empty string, or `None` for a number or a date. Reading never
raises for want of a default.

A changed value reads back as the type its field produces, so a `DateField`
gives a `datetime.date` and a `DecimalField` a `decimal.Decimal`, although the
record stores them as JSON. Change a field's `initial` and every record that has
not stored its own value reads the new default, with no migration and no data
change.

## Contributing

Standards for this repository live in
[CONSTITUTION.md](https://github.com/django-mvp/django-object-preferences/blob/main/CONSTITUTION.md),
and the vocabulary to use in issues and commits lives in
[CONTEXT.md](https://github.com/django-mvp/django-object-preferences/blob/main/CONTEXT.md).

```bash
uv sync
uv run pytest
uv run pre-commit install
```

## License

MIT. See [LICENSE](https://github.com/django-mvp/django-object-preferences/blob/main/LICENSE).
