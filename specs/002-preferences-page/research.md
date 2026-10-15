# Research: A page to change a record's preferences

Done against origin/main at f1acb4b, with FS-001 merged.

## The specification read against what was delivered since

FS-001 (#7) was delivered after this specification was written. Read side by side:

- Every capability this spec's "Builds on" section asks of FS-001 exists as described:
  `registry.get_groups(model)` lists a model's groups, `record.preferences[name]` reads a group's
  values with defaults and the stale-value fallback, `get_form(name, data=..., prefix=...)` binds
  a group's form starting from those values, `apply(name, form)` validates and stores one group in
  memory, and `save()` writes the preferences once with `update_fields`.
- US1-6 (saving an unchanged page leaves nothing stored) holds under FS-001's rule that a value
  equal to its default is not stored, and `apply` removes a group's entry when it ends up empty.
- The edge case about a stored preference that no longer exists defers to FS-001, which drops
  stale keys from a group when that group is applied. No contradiction.
- FR-010 (only the preferences are written) is what FS-001's `save()` already does.

No acceptance scenario here describes behaviour FS-001 changed, and FS-001 delivered nothing this
spec expected to build itself. Nothing goes to Sam.

## Planning notes

### N1. A class-based view that takes its record from `get_object()`

**Adopted.** The page is a subclass of Django's `DetailView`, which already carries
`SingleObjectMixin` (`model`, `queryset`, `get_queryset()`, `get_object()`, the not-found
response) and `SingleObjectTemplateResponseMixin`. The view adds `post()` and the methods that
build and save the forms. Limiting the records it looks up is `queryset=` or `get_queryset()`,
and pointing it at the signed-in person is a `get_object()` that returns `self.request.user`.
Both are what an experienced Django developer would reach for first, which is the README's own
tie-breaker.

Considered and set aside: `UpdateView`, whose `ModelFormMixin` expects one model form for the
record and would write every field the form holds (FR-010); `FormView`, which has no record; and
`View` with the two mixins assembled by hand, which is `DetailView` spelled out.

### N2. Validate every group before writing any of them

**Adopted.** `post()` binds every group's form with its group's name as the prefix, calls
`is_valid()` on every one of them (a list, never a short-circuiting `all()` over a generator, so
every group's errors are shown at once), and only when all are valid calls `apply()` for each and
`save()` once. `apply()` changes the record in memory only, so nothing reaches the database until
the single `save()`. FS-001 exposed `get_form` and `apply` separately for exactly this.

## Settled questions

**Which field carries the preferences.** The field is not always called `preferences`.
`registry.get_field(model)` returns it, and the view reads the record's accessor through that
field's `attname`. It also raises `ImproperlyConfigured` naming the model when the model has no
`PreferencesField`, which is FR-018 with no code of our own.

**The model to ask about.** `self.object._meta.model`, not `type(self.object)`. Story 3 returns
`self.request.user` from `get_object()`, which is a `SimpleLazyObject`. `type()` of it is the
lazy wrapper, while attribute access, `_meta` included, reaches the real user.

**Keeping same-named preferences apart (FR-007).** Each group's form gets `prefix=<group name>`,
so `display-theme` and `other-theme` are separate inputs and separate POST keys. Group names are
unique per model (FS-001), so prefixes never collide.

**Accessible markup (FR-015).** Django's own form rendering already does what the requirement
asks, on every supported version (checked in the installed 6.1 and in 5.2): `{{ form }}` renders
a `<label for>` for every control, puts each field's errors in a list with the id
`<auto_id>_error`, and sets `aria-describedby` and `aria-invalid` on the control that has them.
Radio and checkbox groups get a `<fieldset>` with a `<legend>`. Errors that belong to no single
field render at the top of that group's form. The template adds one `<fieldset>` and `<legend>`
per group around `{{ form }}`, and nothing else is needed.

**What the legend says.** A group has a name and no human label in FS-001. The legend shows the
name with its first letter capitalised. Adding a label to the group would be new public API that
nothing here asks for; a project that wants different words overrides the template, and R4 is
where named restyling points arrive.

**A page with no base template (FR-016).** A Django project has no standard base template, so a
package template that extends one fails in a project that lacks it. The package's template is a
complete HTML document of its own. A project that wants its own layout overrides the template in
the ordinary way. One template, no included partials.

**Messages (FR-009).** `messages.success(request, ..., fail_silently=True)` adds the message when
the messages middleware is installed and does nothing when it is not. Django's own
`SuccessMessageMixin` raises without the middleware, so it is not used. The template shows
`messages` when the context processor provides them, so the confirmation is visible on the
redirected page.

**Where the person goes after saving (FR-008).** `success_url` defaults to `None`, and
`get_success_url()` returns it when set and the request's own path otherwise, which is the same
page. Following Django's `FormMixin`, a set `success_url` may be a lazy URL.

**Refused requests (FR-011, FR-012).** Django's access mixins (`LoginRequiredMixin`,
`PermissionRequiredMixin`, `UserPassesTestMixin`) and the `login_required` and
`permission_required` decorators all refuse in `dispatch()` or before the view runs, so a refused
POST never reaches `post()`, and nothing is read or saved. The view adds no rule and does no work
outside `get()` and `post()`.

**Translatable text (FR-017).** The template loads `i18n` and wraps its own strings, and the
success message is a `gettext_lazy` string on the view. The English catalogue is regenerated with
`makemessages -l en` in `object_preferences/`.

**Test settings.** The suite's settings have no middleware today. The page's tests need sessions,
authentication and messages, so the settings gain those three middleware and the messages app,
all Django's own. A test for FR-009's "works without it" removes the messages middleware with
the `settings` fixture.

**A user model with preferences in the tests (Story 2, Story 3).** Story 3 needs a user model
that carries preferences, and Story 2's "test the person against the record" reads most simply as
"the record is the signed-in person". The test app gains `User(AbstractUser)` with a
`PreferencesField`, `AUTH_USER_MODEL = "testapp.User"`, and one group for it. No installed app
holds a foreign key to the user model (contenttypes, auth, sessions and messages do not), so the
model can arrive in a second test-app migration.

**The example project.** It gains accounts, so the page can be seen behind a sign-in. Its user
model is a custom `User(AbstractUser)` that carries preferences, signs in by email and has two
groups of its own, so the documented "your own preferences" page runs in it as written. Projects
get a page restricted to people with the `change_project` permission, which shows a refusal for a
signed-in person without it. The seed command creates the standard development accounts.

## What already exists

- The page's record lookup, not-found response and template resolution: **Django**,
  `DetailView` (`SingleObjectMixin`, `SingleObjectTemplateResponseMixin`).
- Groups for a model, a group's form bound from the record's values, validating and storing one
  group, writing only the preferences: **this repo**, `registry.get_groups`, `get_form`, `apply`,
  `save` (FS-001).
- The record's preferences field and the error for a model without one: **this repo**,
  `registry.get_field`.
- Labels, error lists with ids, `aria-describedby`, `aria-invalid`, fieldsets for multi-input
  widgets: **Django**, form rendering.
- Access rules: **Django**, `django.contrib.auth.mixins` and `django.contrib.auth.decorators`.
- The success message without requiring the framework: **Django**, `messages.success(...,
  fail_silently=True)`.
- Sign-in pages for the example project: **Django**, `django.contrib.auth.urls`.
- The view's `post()`, `get_forms()`, `get_preferences()`, `forms_valid()`, `forms_invalid()`,
  `get_success_url()`: **new code**, about forty lines, because no Django view edits several
  forms that are not model forms against one record.
- The page's template: **new code**, one file.
