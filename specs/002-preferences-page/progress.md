
## 2026-10-15T12:09:06Z · Forge · S3

Did: picked FS-002 up from the queue (orchestrated run, claim held for this session). Rebased 002-preferences-page onto origin/main f1acb4b. Read the spec against FS-001: no contradiction (research.md). Wrote research.md, plan.md, tasks.md (10 tasks, 3 stories) and the ledger.
Verified: forge verify on a339715 green (lint, typecheck, test, build, conformance, docs). Analyze by hand: every FR-001..019 and SC-001..006 maps to a task; no CRITICAL.
Next: design review (one reviewer, three lenses).
Watch: sessions_spawn failed on FS-001; try it first, fall back to in-turn harness agents in their own worktrees.

## 2026-10-15T12:18:35Z · Implementer US1 · T001

Did: PreferencesView GET (get_preferences, get_forms, get_context_data), the page template, test settings (messages app, middleware, context processor) and routes for Project and Document.
Verified: uv run pytest tests/test_views.py (8 passed); pre-commit run --all-files passed.
Next: T002 saving.
Watch: Document fixture added to conftest.

## 2026-10-15T12:19:28Z · Implementer US1 · T002

Did: post(), forms_valid(), forms_invalid(), get_success_url(); tests for saving, all-or-nothing, clean() error, prefixes, message, no-middleware, success_url, update_fields, Document, CSRF; one extra route in tests/urls.py for success_url.
Verified: uv run pytest tests/test_views.py (19 passed); pre-commit run --all-files passed.
Next: T003 markup.
Watch: the CSRF and unchanged-page tests passed on first run (csrf_protect was already on the class from T001; an unchanged page stores nothing with no code to do it).

## 2026-10-15T12:19:54Z · Implementer US1 · T003

Did: markup tests (label for each control, fieldset with one legend per group, aria-describedby naming the element that holds the error).
Verified: uv run pytest tests/test_views.py::TestPreferencesViewMarkup (3 passed); probe: replacing legend in the template fails the legend test; pre-commit passed.
Next: T004 docs.
Watch: the three tests passed on first run because the template from T001 and Django own form rendering already provide the markup; no production change in this task. The label and aria-describedby tests rest on Django rendering of the form.

## 2026-10-15T12:20:16Z · Implementer US1 · T004

Did: README "The preferences page", CHANGELOG Unreleased entry, CONTEXT.md term, regenerated the English catalogue with makemessages -l en.
Verified: pre-commit run --all-files passed. No page under docs/ describes the view, so none needed changing.
Next: full verify.
Watch: none.

## 2026-10-15T12:21:46Z · Forge · US1

Did: accepted US1 (T001-T004). Implementer ran as an in-turn harness agent (sonnet) in dop-002-us1: sessions_spawn refused every model with "selected account or native runtime is unavailable", as on FS-001; transcripts land under the orchestrator workspace, so dispatched cost is not priced per worktree.
Verified: receipts green; forge verify green on the merged branch (142 tests); tamper-check flags tests/conftest.py and tests/urls.py, both additive (a document fixture, routes).
Next: US2.
Watch: US2 adds AUTH_USER_MODEL=testapp.User; FS-001 tests must stay untouched.

## 2026-10-15T12:23:12Z · Implementer US2 · T005

Did: routed Plain page, PlainFactory, test for ImproperlyConfigured naming testapp.Plain.
Verified: pytest TestPreferencesViewWithoutPreferences, 1 passed. Passed on first run: the behaviour is registry.get_field, already built.
Next: T006 test user.
Watch: none.

## 2026-10-15T12:24:02Z · Implementer US2 · T006

Did: User(AbstractUser) with PreferencesField, AUTH_USER_MODEL, notifications group, UserFactory, user fixture, migration 0002_user.
Verified: pytest -n auto --dist loadscope 143 passed; makemigrations --check clean; pre-commit all files passed.
Next: T007 access tests.
Watch: user fixture unused until T007.
