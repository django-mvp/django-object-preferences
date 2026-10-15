
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
