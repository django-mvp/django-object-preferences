
## 2026-10-15T10:55:27Z · Forge · S3

Did: research.md, plan.md and tasks.md written; ledger created with every task at todo.
Verified: base suite green on 9dc15d8 (1 passed).
Next: design review.
Watch: FS-002 builds on get_groups, record.preferences[name], get_form, apply and save.

## 2026-10-15T11:12:16Z · Implementer US1 · T001

Did: test app (Project, Plain), ProjectFactory, project fixture, testapp in INSTALLED_APPS. migrations/ package deferred to T004 so the unmigrated app is created by syncdb for T003 tests.
Verified: uv run pytest -q, 1 passed; pre-commit all files passed.
Next: T002 PreferencesField.
Watch: Project has no preferences field until T002.

## 2026-10-15T11:13:17Z · Implementer US1 · T002

Did: PreferencesField with defaults and minimal deconstruct; Project carries the field. deconstruct also restores blank/editable when the host overrides to Django default, since Django omits them.
Verified: uv run pytest tests/test_fields.py -q, 5 passed; pre-commit and mypy clean.
Next: T003 descriptor and RecordPreferences.
Watch: autodetector test uses a graph with a stand-in 0001 node because changes() drops apps absent from the graph.

## 2026-10-15T11:14:06Z · Implementer US1 · T003

Did: RecordPreferences (record, field, stored), PreferencesDescriptor, the three unwrapping methods on the field via one static unwrap().
Verified: uv run pytest tests/test_fields.py -q, 14 passed; mutation probe of each unwrapping method: get_prep_value and to_python and value_from_object each fail a test when removed; pre-commit and mypy clean.
Next: T004 migration.
Watch: none.

## 2026-10-15T11:14:38Z · Implementer US1 · T004

Did: generated tests/testapp/migrations/0001_initial.py with makemigrations; added the makemigrations --check --dry-run test. Wrote the migration before the test, then moved it away to observe the test red (SystemExit 1) and restored it.
Verified: uv run pytest tests/test_fields.py -q, 15 passed; pre-commit clean.
Next: T005 README, CHANGELOG, catalogue.
Watch: none.

## 2026-10-15T11:14:57Z · Implementer US1 · T005

Did: README Usage section (turning preferences on, quoting PreferencesField, PreferencesDescriptor, RecordPreferences), CHANGELOG Added entries, locale/en/LC_MESSAGES/django.po via makemessages -l en (locale/ had to be created first). Built a wheel to /tmp and confirmed the .po ships.
Verified: pre-commit all files clean; uv build --wheel lists object_preferences/locale/en/LC_MESSAGES/django.po.
Next: full suite and report.
Watch: no docs/ page describes anything this story touched.

## 2026-10-15T11:17:57Z · Implementer US2 · T006

Did: added registry.py (PreferenceGroup, PreferenceRegistry, registry, register) and the preference_registry fixture, tests first (ImportError red).
Verified: uv run pytest tests/test_registry.py -x, 17 passed; pre-commit all files passed.
Next: T007 discovery.
Watch: git status after ledger/progress writes.

## 2026-10-15T11:18:21Z · Implementer US2 · T007

Did: ready() calls autodiscover_modules("preferences"); tests/testapp/preferences.py registers display and typed groups.
Verified: uv run pytest tests/test_apps.py tests/test_registry.py -x, 18 passed; red first (no groups found).
Next: T008 reading.
Watch: none.

## 2026-10-15T11:19:28Z · Implementer US2 · T008

Did: PreferenceGroup.defaults/read and RecordPreferences as a Mapping of group name to MappingProxyType; tests in TestPreferenceGroup and TestRecordPreferences.
Verified: uv run pytest tests/test_registry.py tests/test_fields.py -q, 55 passed; pre-commit and mypy clean.
Next: T009 makemigrations check.
Watch: read() assumes well-formed stored data until US4.

## 2026-10-15T11:19:37Z · Implementer US2 · T009

Did: added a makemigrations --check --dry-run test after registering and replacing a group.
Verified: uv run pytest tests/test_apps.py -q, 2 passed. It passed on first run: it guards a property that holds by design (groups touch no model), so there was no red step.
Next: T010 README and changelog.
Watch: none.

## 2026-10-15T11:19:59Z · Implementer US2 · T010

Did: README sections on declaring, looking up and reading groups, where a default comes from, and the required-field-with-no-initial case; CHANGELOG entries.
Verified: uv run pre-commit run --all-files passed. No other page under docs/ documents a name or behaviour this story touched.
Next: full suite, pre-commit, mypy, report.
Watch: none.

## 2026-10-15T11:23:33Z · Implementer US3 · T011

Did: RecordPreferences.get_form with tests.
Verified: uv run pytest tests/test_fields.py -k form, 5 passed; pre-commit and mypy clean.
Next: T012 to_stored and apply.
Watch: none.

## 2026-10-15T11:24:32Z · Implementer US3 · T012

Did: PreferenceGroup.to_stored and RecordPreferences.apply with tests.
Verified: uv run pytest tests/test_fields.py tests/test_registry.py, 73 passed; pre-commit and mypy clean.
Next: T013 change.
Watch: the two save-and-reload tests call record.save(), since preferences.save() is T014.

## 2026-10-15T11:25:00Z · Implementer US3 · T013

Did: RecordPreferences.change with tests.
Verified: uv run pytest tests/test_fields.py, 53 passed; pre-commit and mypy clean.
Next: T014 save.
Watch: none.

## 2026-10-15T11:25:24Z · Implementer US3 · T014

Did: RecordPreferences.save with tests.
Verified: uv run pytest tests/test_fields.py, 56 passed; pre-commit and mypy clean.
Next: T015 example project.
Watch: the never-saved test wraps save in transaction.atomic because Django marks the surrounding test transaction for rollback when save raises.

## 2026-10-15T11:26:08Z · Implementer US3 · T015

Did: example project (manage.py, example/ app, seed_example, migration), ignores and deptry exclude.
Verified: migrate OK, seed_example run twice gave 3 projects each time, check exit 0, curl of / on port 8317 returned 200 and listed the three projects with their stored dictionaries. Server stopped.
Next: T016 README and CHANGELOG.
Watch: none.

## 2026-10-15T11:26:30Z · Implementer US3 · T016

Did: README section on changing from code (change, save, get_form, apply, ValidationError) and an Example project section; CHANGELOG entries.
Verified: ran the README change/save/ValidationError snippets in the example project shell; outputs matched the text; pre-commit clean. No other page under docs/ describes this API.
Next: full suite.
Watch: none.

## 2026-10-15T11:30:59Z · Implementer US4 · T017

Did: Wrote the tolerant-read tests first (15 red: AttributeError, TypeError and ValidationError from stale data), then PreferenceGroup.read treats a non-dict as nothing stored and falls back to the default when cleaning raises; RecordPreferences.__getitem__ reads a non-dict root as {}.
Verified: uv run pytest tests/test_registry.py::TestPreferenceGroup tests/test_fields.py::TestRecordPreferences, 82 passed; pre-commit run --all-files passed.
Next: T018 stale value dropped on save.
Watch: contextlib.suppress(Exception) is deliberate, ruff rejects try/except/pass.

## 2026-10-15T11:31:14Z · Implementer US4 · T018

Did: Added the test that a stale stored value is gone after change() and save(). With object_preferences/ taken back to before T017 it fails with ValidationError (change reads the stale value); with T017 it passes.
Verified: uv run pytest tests/test_fields.py -k stale_stored_value_is_not_stored, 1 passed (1 failed with the T017 code removed); pre-commit run --all-files passed.
Next: T019 example, README, CHANGELOG.
Watch: none.

## 2026-10-15T11:31:47Z · Implementer US4 · T019

Did: seed_example adds a fourth project storing theme sepia, which the display form does not offer. README gains "Changing a declaration" and the example section says four projects. CHANGELOG entry under Unreleased.
Verified: migrate, seed_example (4 projects) and check ran clean on a fresh sqlite file; the page fetched on port 8731 showed that project reading display.theme: light, page_size 25. Server stopped, db.sqlite3 removed.
Next: full suite, pre-commit, mypy, report.
Watch: none.
