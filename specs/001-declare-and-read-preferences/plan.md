# Implementation Plan: Declare preferences for a model and read them from its records

**Branch**: `001-declare-and-read-preferences` | **Date**: 2026-10-15 | **Spec**: [spec.md](spec.md)

**Input**: the approved specification, `decisions.md`, and `research.md`, which carries the
evidence for every design choice below.

## Summary

A model field, `PreferencesField`, turns preferences on for a model with one migration. Its
descriptor hands back a `RecordPreferences` accessor that reads each preference group's values
from the record's own stored dictionary, typed and validated by the group's form field, with no
query. Groups are ordinary Django forms registered with `register(model, name=...)` in an app's
`preferences.py`, found by `autodiscover_modules` as the admin finds `admin.py`. Code changes
preferences through the group's form with `change()` or `apply()` and writes them with `save()`,
which touches only the preferences column. An `example/` project and a README usage section show
all of it.

## Technical Context

**Language/Version**: Python 3.12 and 3.13

**Primary Dependencies**: Django 5.2, 6.0 and 6.1. No new dependency, runtime or development.

**Storage**: one JSON column on the host project's model. The package itself has no models and no
migrations.

**Testing**: pytest with pytest-django and factory-boy from the shared bundle. A test app,
`tests/testapp/`, carries the models and groups the tests need.

**Target Platform**: any Django project. SQLite in the suite. Nothing here is backend-specific,
because no query reads inside the JSON.

**Project Type**: a reusable Django package.

**Performance Goals**: reading any number of preferences from a loaded record makes zero queries
(SC-002).

**Constraints**: Django only (Article XII). No leading-underscore names anywhere, line length 88,
no compatibility aliases, no tests of wording or layout.

**Scale/Scope**: four modules, about 300 lines of package code.

## Constitution Check

| Article | How the plan meets it |
|---|---|
| I Testing | Test-first per story. Validation errors asserted by field and code. The query-count check is the zero-query read test. `makemigrations --check` runs over the test app |
| II Simplicity | Two new classes the spec asks for (the registry and the per-record accessor) and two thin subclasses of Django classes. No settings, no signals, no new dependency |
| III Anti-abstraction | No base classes. `PreferenceGroup` is a frozen dataclass of what a registration is |
| IV Integration-first | Every acceptance test goes through the field on a real model, the registry and `record.preferences`, the way a host project does |
| V Security | No rendered output in the package. Stored data is treated as untrusted on read and never raises (FR-016, FR-017) |
| VI Documentation | README usage section and CHANGELOG in this pull request, each story documenting the names it introduces |
| VII Dependencies | None added. `example/` is excluded from deptry, as in django-flex-menus |
| VIII Internationalisation | The field's `verbose_name` and `help_text` and every `ImproperlyConfigured` message use `gettext_lazy` or `gettext` |
| IX Data model | The field supplies `verbose_name` and `help_text` and is deliberately unindexed: preferences have no query path (Article XII). The package ships no migration. The test app's migration and the example's are one file each |
| X Cohesion | Registration lives on `PreferenceRegistry`, a group's reading and storing on `PreferenceGroup`, a record's on `RecordPreferences`. `register` is a thin wrapper over the registry |
| XI Compatibility | First public API, recorded under Unreleased |
| XII Scope | No page, view, URL or permission check. Nothing makes preferences filterable |

Result: passes, nothing in Complexity Tracking.

## Design

### The public API

This is the surface FS-002 builds on. Names and signatures are fixed by this plan.

```python
# object_preferences/fields.py
class PreferencesField(models.JSONField): ...          # PreferencesField() on a model
class PreferencesDescriptor(DeferredAttribute): ...    # installed by the field

class RecordPreferences(Mapping[str, Mapping[str, Any]]):
    record: models.Model
    field: PreferencesField
    stored -> Any                    # property: the record's stored dictionary, as stored
    __getitem__(name) -> Mapping     # one group's values, read-only; KeyError if undeclared
    __iter__() / __len__()           # the names of the groups declared for the record's model
    get_form(name, data=None, **kwargs) -> forms.Form
    apply(name, form) -> None        # ValidationError if invalid, TypeError if wrong form
    change(name, **values) -> None   # KeyError for an undeclared preference
    save() -> None                   # record.save(update_fields=[field.attname])

# object_preferences/registry.py
@dataclass(frozen=True)
class PreferenceGroup:
    model: type[models.Model]
    name: str
    form_class: type[forms.BaseForm]
    defaults(form) -> dict[str, Any]
    read(stored) -> dict[str, Any]
    to_stored(form, encoder) -> dict[str, Any]

class PreferenceRegistry:
    declarations: dict[type[models.Model], dict[str, PreferenceGroup]]
    register(model, name, form_class) -> PreferenceGroup   # ImproperlyConfigured on a mistake
    get_groups(model) -> list[PreferenceGroup]              # in registration order
    get_group(model, name) -> PreferenceGroup               # KeyError if undeclared

registry: PreferenceRegistry
def register(model, *, name) -> Callable[[type[Form]], type[Form]]   # decorator
```

`object_preferences/__init__.py` stays as it is. Imports are from `object_preferences.fields`
and `object_preferences.registry`, which is where a Django developer reading the README will look.

### The field (`fields.py`, US1)

- `PreferencesField.__init__` sets `default=dict`, `blank=True`, `editable=False`,
  `encoder=DjangoJSONEncoder`, `verbose_name=_("preferences")` and a translatable `help_text`
  with `kwargs.setdefault`, so a host can still override any of them.
- `deconstruct()` deletes each of those keys while it holds the field's own value. The host's
  migration reads `PreferencesField()`.
- `descriptor_class = PreferencesDescriptor`. Its `__get__` calls `super().__get__` (which loads a
  deferred value) and returns `RecordPreferences(instance, self.field)`. Its `__set__` unwraps a
  `RecordPreferences` to its `stored` value and writes `instance.__dict__[attname]`, which makes it
  a data descriptor.
- `get_prep_value`, `to_python` and `value_from_object` each unwrap a `RecordPreferences` to its
  `stored` value before Django's own handling (`research.md` §2).
- `RecordPreferences.stored` returns `record.__dict__[field.attname]`. US1 gives the class
  `record`, `field`, `stored` and nothing else. US2 makes it a mapping.

### Registration (`registry.py` and `apps.py`, US2)

- `PreferenceRegistry.register()` raises `ImproperlyConfigured` for a duplicate name on a model,
  a model without a `PreferencesField` among `model._meta.get_fields()`, and a form whose
  `base_fields` hold a `forms.ModelChoiceField` or `forms.FileField`. Each message names what is
  wrong and where (`research.md` §3). It imports `PreferencesField` inside the method, with a
  comment, because `fields.py` imports this module.
- `get_group()` raises `KeyError` naming the group and the model, `app_label.ModelName`.
- `ObjectPreferencesConfig.ready()` calls `autodiscover_modules("preferences")`.

### Reading (`registry.py` and `fields.py`, US2, made tolerant in US4)

- `PreferenceGroup.defaults(form)`: per field, `form.get_initial_for_field(field, name)`, or the
  widget's empty-submission value when that is `None`, passed through `field.clean()`, falling back
  to `field.to_python()` of the same value when cleaning raises `ValidationError`
  (`research.md` §4).
- `PreferenceGroup.read(stored)`: instantiates `form_class()`, takes its defaults, and for each
  field with a key in `stored` uses `field.clean(stored[name])` instead. US2 assumes `stored` is
  a dict of values that clean. US4 adds the tolerance: a value that raises anything on cleaning
  reads as the default, and a `stored` that is not a dict reads as empty.
- `RecordPreferences.__getitem__(name)`: `registry.get_group(type(self.record), name)`, then
  `MappingProxyType(group.read(<the stored dict's entry for name>))`. US4 makes a stored root that
  is not a dict read as empty.
- `__iter__` and `__len__` over `registry.get_groups(type(self.record))` names.

### Changing (`registry.py` and `fields.py`, US3)

- `RecordPreferences.get_form(name, data=None, **kwargs)`: `form_class(data=data,
  initial=dict(self[name]), **kwargs)`, with an `initial` the caller passes laid over the current
  values. Unbound when `data` is `None`.
- `PreferenceGroup.to_stored(form, encoder)`: from `form.cleaned_data`, only the group's declared
  fields, only values that differ from `defaults()` of a fresh `form_class()`, each passed through
  `json.loads(json.dumps(value, cls=encoder))` so the in-memory value equals what the database
  will return.
- `RecordPreferences.apply(name, form)`: `TypeError` unless `isinstance(form,
  group.form_class)`. `ValidationError(form.errors.as_data())` unless `form.is_valid()`. Then a copy
  of the stored dict (a new dict when it is not one) with `stored[name]` replaced by
  `to_stored()`, or removed when that is empty, assigned back through the descriptor.
- `RecordPreferences.change(name, **values)`: `KeyError` for a key not in the group's form
  fields, naming it. Otherwise `apply(name, get_form(name, data={**self[name], **values}))`.
- `RecordPreferences.save()`: `self.record.save(update_fields=[self.field.attname])`.

### Test layout

- `tests/testapp/`: `apps.py`, `models.py` with `Project` (a `name` and `preferences =
  PreferencesField()`) and `Plain` (no preferences), `preferences.py` registering the groups the
  tests read, and `migrations/0001_initial.py`. Added to `INSTALLED_APPS` in `tests/settings.py`.
- `tests/factories.py`: `ProjectFactory`. `Plain` is never instantiated, so it gets no factory.
- `tests/conftest.py`: a `project` fixture wrapping the factory, and a `preference_registry`
  fixture that snapshots `registry.declarations` and restores it after the test, for tests that
  register or replace groups.
- `tests/test_fields.py` (`TestPreferencesField`, `TestRecordPreferences`),
  `tests/test_registry.py` (`TestPreferenceRegistry`, `TestPreferenceGroup`),
  `tests/test_apps.py` (`TestObjectPreferencesConfig`). Mirrors the source tree.
- Validation errors are asserted by field name and code. No test asserts a message's wording.

### Example project (US3, extended in US4)

`manage.py` at the root and `example/`: `settings.py` (SQLite at `example/db.sqlite3`, ignored by
git, `ALLOWED_HOSTS = ["*"]` because it only ever runs locally), `urls.py`, `apps.py`,
`models.py` with a `Project`, `preferences.py` with one `display` group, `views.py` with one
`ListView` of projects, a plain template showing each project's preferences and what it stores,
`management/commands/seed_example.py` creating three projects and changing one's preferences from
code, and `migrations/0001_initial.py`. `pyproject.toml` excludes `example/` from deptry and gives
it the same ruff per-file ignores django-flex-menus does. US4 adds a fourth seeded project with a
stale stored value, so the page shows it reading its default.

## Project Structure

### Documentation (this feature)

```text
specs/001-declare-and-read-preferences/
├── spec.md
├── decisions.md
├── research.md
├── plan.md
├── tasks.md
├── progress.md
└── feature-state.json
```

### Source Code (repository root)

```text
object_preferences/
├── __init__.py
├── apps.py          # ready(): autodiscover_modules("preferences")
├── fields.py        # PreferencesField, PreferencesDescriptor, RecordPreferences
└── registry.py      # PreferenceGroup, PreferenceRegistry, registry, register

tests/
├── settings.py      # + "testapp"
├── conftest.py      # project, preference_registry
├── factories.py     # ProjectFactory
├── testapp/         # apps, models, preferences, migrations
├── test_apps.py
├── test_fields.py
└── test_registry.py

example/             # the example project
manage.py
```

**Structure Decision**: a single package, as the repository already is. `example/` and a root
`manage.py` follow django-flex-menus.

## Complexity Tracking

Nothing to justify.
