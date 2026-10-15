
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
