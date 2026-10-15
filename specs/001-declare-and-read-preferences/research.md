# Research — 001, declare preferences for a model and read them from its records

Investigation run against `origin/main` at `9dc15d8` on 2026-10-15, with Django 6.1.2 resolved in
the project virtualenv. Every claim about Django below cites the installed source under
`.venv/lib/python3.13/site-packages/django/`.

There is no `planning-notes.md` for this feature and no sketch, so the inputs are the
specification, its decisions and the repository as it stands: an app config, a smoke test and the
standards documents. Nothing of the package exists yet.

## 1. How a record carries its preferences

**Decision**: a model field, `PreferencesField`, a subclass of Django's `JSONField`. A host project
turns preferences on by adding it to a model it owns:

```python
class Project(models.Model):
    preferences = PreferencesField()
```

**Why a field and not an abstract model or a mixin**: a field is what "one migration on that
model" means in Django. It costs the host nothing else, works on a custom user model and on any
other model, and does not impose a base class. `makemigrations` produces one `AddField`, and since
the group declarations live in forms, nothing a group does ever changes the field.

**Field defaults, set in `__init__` and dropped again in `deconstruct()`**: `default=dict`,
`blank=True`, `editable=False`, `encoder=DjangoJSONEncoder`, and a translatable `verbose_name` and
`help_text` (Constitution Article IX). `deconstruct()` removes each one while it still holds the
field's own value, so the host's migration reads `PreferencesField()` and a later release of this
package changing the help text does not hand every host project a migration. This is the pattern
Django's own fields use to keep migrations minimal.

- `editable=False` keeps the raw JSON out of every `ModelForm` and the admin. The admin is roadmap
  item R5, and a textarea of JSON would invite edits that skip the group's validation.
- `default=dict` means existing rows get `{}` when the column is added, which is how records that
  already exist "hold no stored values" (US1, scenario 2).
- **No index** (Article IX). Preferences have no query path: Article XII rules out filtering or
  ordering records by them.
- `DjangoJSONEncoder` is what lets a date, a decimal, a duration or a UUID be stored at all.

## 2. How reading reaches the record without a query

**Decision**: the field installs a descriptor, `PreferencesDescriptor`, subclassing Django's
`DeferredAttribute`, that returns a `RecordPreferences` object wrapping the record. The raw stored
dictionary stays in `instance.__dict__` exactly where Django puts any field's value.

This is the shape Django uses for `FileField`: `FileDescriptor(DeferredAttribute)` returns a
`FieldFile` around the stored name (`db/models/fields/files.py:159`) and defines `__set__`
(`files.py:235`) so that it is a data descriptor. That last point is load-bearing:
`DeferredAttribute` defines only `__get__` (`db/models/query_utils.py:250-280`), so without a
`__set__` the value in the instance's `__dict__` would shadow the descriptor and the wrapper would
never be returned.

Because the stored dictionary arrives with the row, every read is a dictionary lookup plus the
declaring form's own field cleaning. No query is made (FR-006).

Three methods of the field unwrap the accessor back to its stored dictionary, because each reads
the attribute through the descriptor:

| Method | Who calls it | Source |
|---|---|---|
| `get_prep_value` | `get_db_prep_value` on every save and lookup | `db/models/fields/json.py:101-103` |
| `to_python` | `Field.clean`, before `JSONField.validate` serialises the value, so `full_clean()` works | `db/models/fields/__init__.py:798`, `json.py:128` |
| `value_from_object` | serialisers and `model_to_dict` | `db/models/fields/__init__.py:1191` |

## 3. How a group is declared and found

**Decision**: a preference group is an ordinary `forms.Form` registered against a model under a
name, with a decorator modelled on `admin.register`:

```python
# myapp/preferences.py
from object_preferences.registry import register

@register(Project, name="display")
class DisplayPreferences(forms.Form):
    theme = forms.ChoiceField(choices=THEMES, initial="light")
```

- `PreferenceGroup`, a frozen dataclass of `model`, `name` and `form_class`, is one registration.
- `PreferenceRegistry` holds them, keyed by model and then by name, and is the extension point
  (Article X). `registry` is its one instance and `register` a thin decorator over
  `registry.register`, as `admin.register` is over `admin.site.register`.
- Discovery: `ObjectPreferencesConfig.ready()` calls
  `django.utils.module_loading.autodiscover_modules("preferences")` (`utils/module_loading.py:38`),
  the function the admin uses for `admin.py`. The host project lists nothing (FR-005).
- **A group applies to exactly the model it was registered for** (spec, edge cases). The accessor
  looks groups up by `type(record)`, so a child model does not inherit a parent's groups until R3.

**Registration mistakes raise `ImproperlyConfigured` from `register()`**, which runs inside
`ready()` and so stops the project from starting (FR-019):

- the model already has a group under that name: the error names the model, the name and both
  form classes;
- the model has no `PreferencesField`: the error names the model and the group;
- the form declares a `ModelChoiceField` (and so `ModelMultipleChoiceField`) or a `FileField` (and
  so `ImageField`): the error names the group and the field.

A system check was considered and rejected: checks run for `runserver`, `check` and `migrate` but
not for every entry point, and they can be silenced. The spec asks for a project that refuses to
start.

The model check uses `model._meta.get_fields()`, which needs the model registry loaded. That holds
inside `ready()`, which is where registrations are imported.

`fields.py` imports `registry.py` for lookups. `registry.py` needs `PreferencesField` for the
model check, so it imports it inside `register()`, with a one-line comment naming the cycle.

## 4. What a read returns

`record.preferences` is a read-only mapping of group name to that group's values:

- `record.preferences["display"]["theme"]` reads one preference. The same path works in a
  template as `{{ project.preferences.display.theme }}`, because the template engine tries a
  dictionary lookup first.
- A group's values are returned as a `types.MappingProxyType` over a fresh dict: read-only, and a
  missing key raises `KeyError` naming it.
- Iterating `record.preferences` gives the names of the groups declared for the model.
- An undeclared group raises `KeyError` naming the group and the model (FR-009).

**Reading one group** (`PreferenceGroup.read(stored)`, given whatever is stored under the group's
name):

1. Instantiate the form with no arguments, so a form that adjusts its fields in `__init__` is read
   the way it is shown.
2. For each field, the default is the form's own initial value
   (`Form.get_initial_for_field`, `forms/forms.py:414`). With none, it is what the field's widget
   reads from an empty submission (`widget.value_from_datadict({}, {}, name)`), so an unticked box
   for a checkbox and nothing for an optional text field. The default is then passed through
   `field.clean()` so it has the type a stored value would. If cleaning rejects it, the field's
   `to_python()` of the same value is used, so a required field without an initial value still has
   a default.
3. A stored value present for the field is passed through `field.clean()`. That restores the type
   (FR-008) and checks the value against the current declaration in the same step (FR-016).

Probed in the installed Django, every field type the spec names round-trips through
`DjangoJSONEncoder` and back through `field.clean()` to an equal value: date, time, duration,
decimal, UUID, multiple choice, typed choice, boolean and `forms.JSONField`. The one loss is a
datetime, which the encoder truncates to milliseconds. ISO dates and times parse whatever the
active locale because `get_format` appends `ISO_INPUT_FORMATS` (`utils/formats.py:19,133`).

**Stale and malformed data never raises** (FR-016, FR-017, SC-004). Cleaning a value of the wrong
shape does not always raise `ValidationError`: `DateField.clean({"a": 1})` and
`TimeField.clean([1])` raise `AttributeError` from inside `to_python`. So a stored value that fails
to clean for any reason reads as the default, and anything stored under the group that is not a
dict, or a stored root that is not a dict, reads as nothing stored. A read never touches the form's
`clean()` or its `clean_<field>()` methods: each preference is checked on its own (spec, edge
cases).

## 5. How code changes and saves preferences

Three methods on `RecordPreferences`, so that code and the later editing page (FS-002) go through
the same path:

- `get_form(name, data=None, **kwargs)` returns the group's form with the record's current values
  as its `initial`, bound to `data` when it is given.
- `apply(name, form)` validates a bound form of that group. Invalid: raises
  `ValidationError(form.errors.as_data())`, which keeps each field's error and its code under the
  field's name, and the form's own `clean()` errors under `NON_FIELD_ERRORS`. Valid: replaces the
  group's stored entry with the cleaned values that differ from their defaults, made JSON-ready
  through the field's encoder. A group left with nothing stored is removed. Nothing else on the
  record changes. A form of another class raises `TypeError`.
- `change(name, **values)` is `apply()` on a form bound to the group's current values with
  `values` laid over them. An undeclared preference name raises `KeyError` naming it.

Binding Python values as form data works for every field type above because each field's
`to_python` accepts its own Python type and each standard widget's `value_from_datadict` reads a
plain dict. Validation is then exactly the form's (FR-011 to FR-014). Replacing the group's whole
entry is what drops its stale and undeclared values on save (FR-018), and leaving every other key
of the stored dictionary alone is what keeps other groups, declared or not, untouched (FR-015).

`save()` calls `record.save(update_fields=[field.attname])`, so other unsaved changes on the record
stay unsaved (US3, scenario 5). An unsaved record raises Django's own `ValueError` from
`save(update_fields=...)`, which is the "saving needs the record to exist" edge case.

FS-002's page needs all groups saved or none. It can bind every group's form, check them all, and
only then `apply()` each and `save()` once. That is why `apply()` is public rather than folded into
`change()`.

**Concurrent saves** stay an open risk, as the specification records. A guard would need a
version column or a database lock, and neither is cheap.

## 6. The example project and the README

**Decision**: an `example/` Django project with a root `manage.py`, the layout django-flex-menus
and django-easy-icons already use in this organisation. It holds one model with preferences, one
group in `example/preferences.py`, a `seed_example` management command that creates records and
changes a preference from code, and one page listing the records with their preferences read from
each record. It depends on Django and this package only, uses SQLite, and is excluded from deptry
and from the package build.

The README gains a usage section quoting every public name, which is what the documentation gate
reads (FR-020, SC-005).

## What already exists

| New piece | Where the search stopped |
|---|---|
| Storage for a record's values | Django: `models.JSONField` is subclassed, not rebuilt |
| Encoding dates, decimals, durations, UUIDs | Django: `DjangoJSONEncoder` |
| Returning an object from a field attribute | Django: the `FileDescriptor` pattern over `DeferredAttribute` |
| Type, validation, choices and default of a preference | Django: `forms.Form` and its fields |
| Restoring a stored value's type and checking it | Django: `forms.Field.clean` |
| Finding `preferences.py` in installed apps | Django: `autodiscover_modules` |
| A read-only view of a group's values | Standard library: `types.MappingProxyType` |
| Validation errors carrying codes per field | Django: `ValidationError` from `form.errors.as_data()` |
| Writing one column | Django: `save(update_fields=...)` |
| Registering a group against a model | New code: `PreferenceRegistry`, `PreferenceGroup`, `register`. Searched: Django has no generic registry, and django-dynamic-preferences registers its own preference classes rather than forms |
| The per-record accessor | New code: `RecordPreferences`. Nothing installed reads typed values out of a JSON field through a form |
| The model field and its descriptor | New code: `PreferencesField`, `PreferencesDescriptor`, each a thin subclass of the Django class named above |
| The example project | New code, following django-flex-menus' `example/` layout |
