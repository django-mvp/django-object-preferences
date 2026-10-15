# Tasks: A page to change a record's preferences

**Input**: `spec.md`, `plan.md`, `research.md` and `decisions.md` in this directory.

**Tests**: every task that changes behaviour is test-first. Tests mirror the source tree
(`object_preferences/views.py` → `tests/test_views.py`), live in `Test<Subject>` classes, build
records through `tests/factories.py`, assert validation errors by field and code and messages by
level, and never assert wording or layout.

**Organisation**: one phase per user story, built in order. Each story's documentation task is in
that story, because the documentation gate reads every story's diff.

## Format: `[ID] [Story] Description`

## Phase 1: User Story 1 — A user changes a record's preferences on its page (P1, #15)

**Goal**: a routed page shows every group of a record's model and saves them all or none.

**Independent test**: route the page for `Project` with no rule, open it for one record, submit
changed values and read the record back.

- [ ] T001 [US1] Test settings and route: `tests/settings.py` gains `django.contrib.messages` and
  the session, authentication and messages middleware; `tests/urls.py` routes
  `PreferencesView.as_view(model=Project)` at `projects/<int:pk>/preferences/`, and the same for
  `Document` (preferences, no groups). `PreferencesView` in `object_preferences/views.py` with
  `get_preferences()`, `get_forms()` and `get_context_data()` per plan.md "The view", and the
  template per plan.md "The template". Tests in `tests/test_views.py` `TestPreferencesView`: the
  page has a bound-to-nothing form for every group of `Project` with a control for every
  preference (US1-1, FR-002); a changed preference starts from its stored value and every other
  from its default (US1-2, FR-003); a stored value that no longer fits starts from the default and
  the page opens (US1-3); controls of two groups carry the group's prefix (FR-007); the page
  renders with the package's own template (FR-016); a `Document` page opens with no controls
  (edge case); a record that does not exist is a 404 (US2-5, FR-013).
- [ ] T002 [US1] Saving: `post()`, `forms_valid()`, `forms_invalid()`, `get_success_url()` per
  plan.md. Tests: changes in two groups are both stored and the response redirects to the same
  page (US1-4, FR-008); an invalid value in one group and a valid change in another stores
  nothing, re-renders with the error on that field by code and both entered values in place
  (US1-5, FR-004, FR-005, FR-006); a group-level error from a form's `clean()` is shown for the
  group (FR-006); saving an unchanged page leaves nothing stored (US1-6); two groups declaring a
  preference of the same name keep their own values (US1-7, FR-007); a
  success message is added (US1-8, FR-009) and saving works with the messages middleware removed
  (FR-009); `success_url` set on the view is where the person is sent (FR-008); the save writes
  the preferences field only (US1-9, FR-010, by `update_fields` seen in a `post_save` receiver);
  saving a `Document` page changes nothing (edge case); a POST without a CSRF token is refused
  with 403 even when the project has no CSRF middleware (D14, `Client(enforce_csrf_checks=True)`
  with the middleware removed by the `settings` fixture). The extra groups US1-7 and the
  group-level error need (a group with a preference named like one in `display`, a group whose
  form's `clean()` raises with a code) are registered inside those tests with the
  `preference_registry` fixture, as `tests/test_fields.py` already does, never in
  `tests/testapp/preferences.py`: three existing tests pin `Project`'s groups (design review
  SPEC-001).
- [ ] T003 [US1] Accessible markup (FR-015). Tests: every control has a `<label>` whose `for` is
  the control's id; each group is a `<fieldset>` with a `<legend>`; after an invalid save the
  invalid control's `aria-describedby` names an element that holds its error. Find elements by id
  and role, not by text.
- [ ] T004 [US1] Documentation: README "The preferences page" opening section per plan.md
  "Documentation" (Story 1 part), quoting `PreferencesView`; CHANGELOG under Unreleased;
  `CONTEXT.md` gains **preferences page**; regenerate `object_preferences/locale/en/LC_MESSAGES/
  django.po` with `makemessages -l en` run in `object_preferences/`.

**Checkpoint**: the page works with no rule and the suite is green.

## Phase 2: User Story 2 — A developer adds the page and decides who may use it (P1, #16)

**Goal**: the page composes with Django's ordinary access tools and refuses the way they refuse.

**Independent test**: route the page with a rule that admits only the record's owner, and open and
submit it as the owner, another person and an anonymous visitor.

- [ ] T005 [US2] A model without preferences (FR-018). Route `PreferencesView.as_view(model=Plain)`.
  Test: opening it raises `ImproperlyConfigured` whose message names the model's label (US2-7).
- [ ] T006 [US2] A test user model: `User(AbstractUser)` with a `PreferencesField` in
  `tests/testapp/models.py`, `AUTH_USER_MODEL = "testapp.User"`, a group registered for it in
  `tests/testapp/preferences.py`, `UserFactory` in `tests/factories.py`, a `user` fixture in
  `tests/conftest.py`, and the test app migration for it. The inherited `AbstractUser` fields
  carry no `help_text`; the model is not packaged, so no field-metadata test covers it.
- [ ] T007 [US2] Access rules, in `tests/urls.py` and `tests/testapp/views.py`: `login_required`
  around the `Project` page; `permission_required("testapp.change_project", raise_exception=True)`
  around it; a `UserPassesTestMixin` subclass for `User` records admitting only the record itself;
  a `Project` page with `queryset` limited to some records. Tests in `tests/test_views.py`, a
  class per concern: an anonymous visitor is redirected to `settings.LOGIN_URL` and the response
  carries no form (US2-1, FR-012); a signed-in person refused by the record test gets 403 on GET
  (US2-2) and on POST, with the record's stored preferences unchanged (US2-3, FR-012); the owner
  can open and save; a person without the permission gets 403 and one with it can save; a record
  outside the limited queryset is a 404 (US2-4, FR-013).
- [ ] T008 [US2] Documentation: README "Who may use the page" per plan.md (Story 2 part), with
  the warning that a page with no rule is open to anyone who can reach it (FR-019) and the error
  for a model without preferences; CHANGELOG line if the entry needs it.

## Phase 3: User Story 3 — A page for each signed-in person's own preferences (P2, #17)

**Goal**: one address where each signed-in person changes their own preferences, documented as
the common case.

**Independent test**: follow the documented example, sign in as two people in turn, and check each
sees and changes only their own.

- [ ] T009 [US3] README "A page for each person's own preferences" (FR-014) and the same view in
  `tests/testapp/views.py`, verbatim apart from imports, routed at `preferences/`. Tests: a
  signed-in person sees their own stored value (US3-1); saving changes their record and not
  another person's (US3-2); an anonymous visitor is redirected to sign in (US3-3).
- [ ] T010 [US3] The example project per plan.md "The example project": user model, groups,
  settings, URLs, sign-in template, links, seed accounts, migration. README "Example project"
  rewritten to say what it now shows and how to sign in. Verified by running `migrate`,
  `seed_example` and `check`, and by opening each page with the development server.

**Checkpoint**: every story green, the documentation describes the branch as it stands.
