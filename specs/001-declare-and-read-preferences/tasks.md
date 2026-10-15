# Tasks: Declare preferences for a model and read them from its records

**Input**: `spec.md`, `plan.md`, `research.md` and `decisions.md` in this directory.

**Tests**: every task that changes behaviour is test-first. Tests mirror the source tree, live in
`Test<Subject>` classes, build records through `tests/factories.py`, and assert validation errors
by field and code, never by wording.

**Organisation**: one phase per user story, built in order. Each story's documentation task is in
that story, because the documentation gate reads every story's diff.

## Format: `[ID] [Story] Description`

## Phase 1: User Story 1 — A developer turns preferences on for a model (P1, #11)

**Goal**: a model gains preferences with one migration, and every record starts with nothing
stored.

**Independent test**: add the field to a test model, check the migration it produces, create and
reload records and read back what they store.

- [ ] T001 [US1] Test app scaffold: `tests/testapp/` with `__init__.py`, `apps.py`, `models.py`
  (`Project` with a `name`, `Plain` with a `name`), `migrations/`; add `"testapp"` to
  `INSTALLED_APPS` in `tests/settings.py`; `tests/factories.py` with `ProjectFactory`;
  a `project` fixture in `tests/conftest.py` wrapping it.
- [ ] T002 [US1] `PreferencesField` in `object_preferences/fields.py` with the defaults and the
  minimal `deconstruct()` from plan.md "The field". Tests in `tests/test_fields.py`
  `TestPreferencesField`: Django's migration autodetector, comparing the test app's state without
  and with the field on `Project`, produces exactly one migration holding one `AddField` on
  `testapp.Project` and nothing else (US1-1, FR-001); `deconstruct()` returns no keyword
  arguments; the field has a `verbose_name` and a `help_text` (presence, not wording); a
  `ModelForm` built for `Project` with `fields="__all__"` has no field for it.
- [ ] T003 [US1] `PreferencesDescriptor` and the first slice of `RecordPreferences` (`record`,
  `field`, `stored`), plus the three unwrapping methods, per plan.md "The field". Tests: a new
  record and a record reloaded from the database both store `{}` (US1-2, FR-002); a stored
  dictionary assigned to the attribute is saved and reloaded unchanged; assigning one record's
  `preferences` to another copies the stored dictionary; `full_clean()` passes on a record.
- [ ] T004 [US1] `tests/testapp/migrations/0001_initial.py` generated with the field on `Project`.
  Test: `makemigrations --check --dry-run` reports no changes for the test app.
- [ ] T005 [US1] README: a usage section opening with turning preferences on, quoting
  `PreferencesField`, `PreferencesDescriptor` and `RecordPreferences`. CHANGELOG under
  Unreleased.

**Checkpoint**: the field works on its own and the suite is green.

## Phase 2: User Story 2 — A developer declares a preference group and reads it from a record (P1, #12)

**Goal**: an app registers a form against a model, the package finds it, and any record reads its
values typed, defaulted and without a query.

**Independent test**: declare groups in the test app, load a record, read every preference, and
count queries.

- [ ] T006 [US2] `PreferenceGroup`, `PreferenceRegistry`, `registry` and `register` in
  `object_preferences/registry.py`, per plan.md "Registration". Tests in
  `tests/test_registry.py` `TestPreferenceRegistry`, each on a fresh `PreferenceRegistry()`: a
  registration is returned by `get_group()` and listed by `get_groups()` with its name and form
  class (US2-7, FR-010); `register` used as a decorator returns the form class unchanged;
  `ImproperlyConfigured` for a duplicate name on one model, for a model without the field
  (`Plain`), for a `ModelChoiceField`, a `ModelMultipleChoiceField`, a `FileField` and an
  `ImageField` (FR-019); `get_group()` raises `KeyError` for an undeclared name (FR-009). Also the
  `preference_registry` fixture in `tests/conftest.py`.
- [ ] T007 [US2] Discovery: `ObjectPreferencesConfig.ready()` calls
  `autodiscover_modules("preferences")`. `tests/testapp/preferences.py` registers a `display` group
  for `Project` (`theme`: `ChoiceField` with an initial value; `page_size`: `IntegerField` with an
  initial value, `min_value` and `max_value`; `show_archived`: `BooleanField(required=False)`)
  and a `typed` group (a `DateField`, `TimeField`, `DecimalField`, `DurationField`, `UUIDField`
  and `MultipleChoiceField`, some without initial values). Test in `tests/test_apps.py`
  `TestObjectPreferencesConfig`: both groups are in `registry.get_groups(Project)` with the test
  settings naming neither (US2-1, FR-004, FR-005).
- [ ] T008 [US2] Reading, per plan.md "Reading" (the US2 part, assuming well-formed stored data):
  `PreferenceGroup.defaults()` and `read()`, and `RecordPreferences` as a mapping. Tests in
  `TestPreferenceGroup` and `TestRecordPreferences`: an unchanged preference reads its field's
  initial value, and a field with none reads the value an empty submission gives (US2-2, FR-007);
  a stored value reads back as the field's type, one test per type in the `typed` group (US2-3,
  FR-008); reading every preference of both groups from a loaded record runs zero queries under
  `django_assert_num_queries(0)` (US2-4, FR-006, SC-002); replacing the `display` group with a form
  whose initial value differs changes what a record with nothing stored reads, while a record that
  stored its own value still reads it (US2-5, FR-007, SC-003); an undeclared group and an
  undeclared preference each raise `KeyError` naming it (US2-6, FR-009); iterating
  `record.preferences` gives the declared group names; a group's values cannot be assigned to.
- [ ] T009 [US2] Test: with groups registered, and after registering and replacing a group
  through `preference_registry`, `makemigrations --check --dry-run` still reports nothing
  (US1-3, FR-003, SC-001).
- [ ] T010 [US2] README: declaring a group in `preferences.py` and reading it, quoting
  `register`, `registry`, `PreferenceRegistry`, `PreferenceGroup`, `get_groups` and `get_group`,
  and saying what the default is. CHANGELOG.

**Checkpoint**: a host project can declare and read preferences.

## Phase 3: User Story 3 — A developer changes and saves a record's preferences from code (P2, #13)

**Goal**: code changes preferences through the group's form, and saving writes only the
preferences.

**Independent test**: change preferences on a record, reload it and read them back; submit an
invalid value and confirm nothing changed.

- [ ] T011 [US3] `RecordPreferences.get_form()`. Tests: unbound, its `initial` holds the record's
  current values; bound to data, it validates that data.
- [ ] T012 [US3] `PreferenceGroup.to_stored()` and `RecordPreferences.apply()`. Tests: a valid
  form's values are stored and read back after `save()` and a reload, a date and a decimal
  included (US3-1, FR-011); a value equal to its default leaves nothing stored and removes what
  was stored, and a later change of default reaches the record (US3-4, FR-014); an invalid form
  raises `ValidationError` whose `error_dict` carries the field's name and error code, and the
  record's stored dictionary is unchanged (US3-3, FR-013); a form whose own `clean()` rejects the
  combination raises with the error under `NON_FIELD_ERRORS`; a form of another class raises
  `TypeError`; applying one group leaves another group's stored values, and a stored group that is
  no longer declared, untouched (US3-6, FR-015); a key stored under the group that the form does
  not declare is gone after applying (FR-018).
- [ ] T013 [US3] `RecordPreferences.change()`. Tests: changing one preference keeps the group's
  others (US3-2, FR-012); an undeclared preference raises `KeyError` naming it, and nothing
  changes.
- [ ] T014 [US3] `RecordPreferences.save()`. Tests: a change saved and reloaded reads the new value
  (US3-1); another field changed on the record but not saved is still the old value in the
  database after `save()` (US3-5, FR-015); saving a record that was never saved raises and writes
  nothing.
- [ ] T015 [US3] The example project, per plan.md "Example project": root `manage.py`,
  `example/` with settings, URLs, app, model, `preferences.py`, list view and template,
  `seed_example` command and migration; `example/db.sqlite3` in `.gitignore`; `pyproject.toml`
  excludes `example/` from deptry and adds its ruff per-file ignores. Verified by running
  `migrate`, `seed_example`, `check` and requesting the page, recorded as evidence (FR-020,
  SC-005).
- [ ] T016 [US3] README: changing preferences from code and saving them, quoting `get_form`,
  `apply`, `change` and `save`, and how to run the example project. CHANGELOG.

**Checkpoint**: preferences can be declared, read, changed and saved, and the example runs.

## Phase 4: User Story 4 — A developer changes a declaration without breaking existing records (P2, #14)

**Goal**: no stored data, however stale or malformed, makes a read raise.

**Independent test**: store values, change the declaring form so some no longer fit, and read
every preference.

- [ ] T017 [US4] Tolerant reads, per plan.md "Reading" (the US4 part). Tests, each replacing a
  group through `preference_registry` or writing the stored dictionary directly: a stored value
  outside narrowed choices, above a lowered maximum, and of a changed type each read as the
  current default (US4-1, FR-016); a stored value of a shape that makes the field's cleaning raise
  something other than `ValidationError` (a dict for a `DateField`) reads as the default; a stored
  preference no longer declared is ignored and the group reads normally (US4-2, FR-017); a stored
  group no longer declared is ignored while every declared group reads (US4-3, FR-017); a stored
  root that is not a dict, and a group entry that is not a dict, read as defaults (US4-4, FR-017,
  SC-004); a stored combination the form's `clean()` now rejects still reads value by value.
- [ ] T018 [US4] Test: a record with a stale stored value in a group, changed validly in that
  group and saved, no longer stores the stale value (US4-5, FR-018). Red until T017.
- [ ] T019 [US4] Example: `seed_example` adds a project whose stored value no longer fits, so the
  page shows it reading its default. README: what happens when a declaration changes. CHANGELOG.

**Checkpoint**: the feature is complete.

## Dependencies and order

- Stories run in order, one at a time: US2 reads through the field US1 adds, US3 changes what US2
  reads, US4 hardens US2's reads and depends on US3's `apply()` for T018.
- Inside each story, tests come before the code that makes them pass.
- Convergence after US4: migration consolidation for the test app and the example, the
  simplification pass, ADR graduation and the roadmap status line.

## Coverage of the specification

| Requirement | Tasks |
|---|---|
| FR-001 | T002 |
| FR-002 | T003, T012 |
| FR-003 | T009 |
| FR-004, FR-005 | T007 |
| FR-006 | T008 |
| FR-007, FR-008 | T008 |
| FR-009 | T006, T008, T013 |
| FR-010 | T006 |
| FR-011 to FR-014 | T012, T013 |
| FR-015 | T012, T014 |
| FR-016, FR-017 | T017 |
| FR-018 | T012, T018 |
| FR-019 | T006 |
| FR-020 | T005, T010, T015, T016, T019 |
| SC-001 | T009 |
| SC-002 | T008 |
| SC-003 | T008, T012 |
| SC-004 | T017 |
| SC-005 | T015, T016 |
