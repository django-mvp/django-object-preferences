
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
