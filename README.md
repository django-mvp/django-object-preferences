# django-object-preferences

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
