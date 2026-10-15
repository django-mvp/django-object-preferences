# django-object-preferences

[![Tests](https://github.com/django-mvp/django-object-preferences/actions/workflows/tests.yml/badge.svg)](https://github.com/django-mvp/django-object-preferences/actions/workflows/tests.yml)
[![Build](https://github.com/django-mvp/django-object-preferences/actions/workflows/build.yml/badge.svg)](https://github.com/django-mvp/django-object-preferences/actions/workflows/build.yml)
[![Publish](https://github.com/django-mvp/django-object-preferences/actions/workflows/publish.yml/badge.svg)](https://github.com/django-mvp/django-object-preferences/actions/workflows/publish.yml)
[![Coverage](https://codecov.io/gh/django-mvp/django-object-preferences/branch/main/graph/badge.svg)](https://codecov.io/gh/django-mvp/django-object-preferences)
[![PyPI](https://img.shields.io/pypi/v/django-object-preferences)](https://pypi.org/project/django-object-preferences/)
[![Development status](https://img.shields.io/pypi/status/django-object-preferences)](https://pypi.org/project/django-object-preferences/)
[![Python](https://img.shields.io/pypi/pyversions/django-object-preferences)](https://pypi.org/project/django-object-preferences/)
[![Django](https://img.shields.io/pypi/djversions/django-object-preferences)](https://pypi.org/project/django-object-preferences/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Licence](https://img.shields.io/github/license/django-mvp/django-object-preferences)](https://github.com/django-mvp/django-object-preferences/blob/main/LICENSE)

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

## Requirements

- Python 3.12 or later.
- Django 5.2, 6.0 or 6.1.

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

### Changing preferences from code

`change` sets some of a group's preferences and leaves the rest as they were.
It validates the values with the group's form, and it changes the record in
memory only, so `save` writes it:

```python
project.preferences.change("display", theme="dark", page_size=50)
project.preferences.save()
```

`save` writes only the preferences, with `update_fields`, so another field you
changed on the record and have not saved is left alone. Calling it on a record
that has no primary key raises a `ValueError`, and on one whose key is set but
that has no row (a UUID key is set before the first save) raises a
`DatabaseError`. A preference changed to its default
has no stored value afterwards, so `change("display", theme="light")` removes
`theme` from what the record stores. Asking to change a preference or a group
that was never declared raises a `KeyError` that names it.

A value the form rejects raises Django's `ValidationError`, and the record is
left as it was. Its `error_dict` is keyed by field name, and an error from the
form's own `clean()` is under `NON_FIELD_ERRORS`. Each error carries the code
the form gave it, which is what to test for rather than the message:

```python
from django.core.exceptions import ValidationError

try:
    project.preferences.change("display", page_size=3)
except ValidationError as error:
    error.error_dict["page_size"][0].code  # "min_value"
```

To work with a whole submission, use the group's form itself. `get_form`
returns the group's form starting from the record's current values, bound to
`data` when you pass it, and `apply` validates a bound form and stores its
values on the record. Both work on their own, so a page can bind the form of
every group, check them all, then `apply` each and `save` once:

```python
form = project.preferences.get_form("display", data=request.POST, prefix="display")
if form.is_valid():
    project.preferences.apply("display", form)
    project.preferences.save()
```

`apply` raises a `TypeError` for a form that is not the group's own, a
`ValueError` for a form bound to no data, and the same `ValidationError` as
`change` for an invalid one. Applying a group
replaces that group's stored values and leaves every other group alone, and it
drops stored keys that the group no longer declares. A `JSONField` preference is
stored as the JSON text its form field shows, and reads back as the value you
set.

### Changing a declaration

Records keep what they stored when you change a form, so removing, renaming or
tightening a preference never needs a data migration. Reading never raises
because of what is stored:

- A stored value the field no longer accepts reads the default. That covers a
  choice you removed, a number above a lowered maximum and a value of a changed
  type, including one the new field would only accept by converting it, such as
  a list stored for what is now a text field.
- A stored preference or group that is no longer declared is ignored. It stays
  in the stored dictionary until its group is saved.
- A stored dictionary, or a group's entry in it, that is not a dictionary reads
  as if nothing were stored.
- Values are read one by one, so a stored combination that the form's `clean()`
  would now reject still reads value by value.

Saving a group with `change` or `apply` rewrites that group's stored values
from the form, so its stale values are cleared. Other groups are left alone.
Renaming a preference therefore reads the new name's default until a person sets
it again.

## The preferences page

`PreferencesView` is a page where a person changes a record's preferences. The
package ships no URL, so you route it in your own `urls.py` and name the model
with `as_view(model=...)`:

```python
# urls.py
from django.urls import path
from object_preferences.views import PreferencesView
from projects.models import Project

urlpatterns = [
    path(
        "projects/<int:pk>/preferences/",
        PreferencesView.as_view(model=Project),
        name="project-preferences",
    ),
]
```

It is a Django `DetailView`, so the record is found by `pk` or `slug`, an
unknown record is a 404, and `queryset` or `get_queryset()` limits which
records the page can open. The page shows every group declared for the model as
a fieldset of its own, each control starting from the stored value or the
default. A model with no preference field raises `ImproperlyConfigured` naming
the model, and a record whose model declares no groups opens with no controls.

Saving is all or nothing. The page validates every group with its own form. If
any is invalid it saves nothing and shows the page again with the values the
person entered and every error at once. Otherwise it applies each group and
writes the preferences with one `save`, which touches no other field. Groups
that declare a preference of the same name keep separate values, because each
group's controls are prefixed with the group's name.

After a save the person is sent back to the same page. Set `success_url` to
send them elsewhere:

```python
PreferencesView.as_view(model=Project, success_url="/projects/")
```

A success message is added at the `SUCCESS` level when Django's messages
framework is installed, and saving works without it. Change the wording with
`success_message`.

The page is the template `object_preferences/preferences_form.html`, a plain
HTML document with no styling. To use your own, put a template of that name
earlier on the template path, or set `template_name` on the view. It receives
`record`, the record, and `forms`, a dictionary of each group's form by group
name. Render each form inside its own `<fieldset>`, and include
`{% csrf_token %}` in the `<form>`. The view checks the token itself, so a
forged post is refused even when the CSRF middleware is not installed.

The page applies no access rule of its own. Who may open it is yours to decide.

## Example project

The repository holds a small Django project in `example/` that declares a
group, reads it and changes it from code. From a checkout:

```bash
uv run python manage.py migrate
uv run python manage.py seed_example
uv run python manage.py runserver
```

Open the address it prints to see four projects, the preferences each one
reads and the dictionary each one stores, which holds only what was changed.
The last project stored a theme that the form no longer offers, so it reads the
default theme while the stored column still shows the old value.

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

## Changelog

See [CHANGELOG.md](https://github.com/django-mvp/django-object-preferences/blob/main/CHANGELOG.md).

## License

MIT. See [LICENSE](https://github.com/django-mvp/django-object-preferences/blob/main/LICENSE).
