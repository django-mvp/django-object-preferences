# Implementation Plan: A page to change a record's preferences

**Branch**: `002-preferences-page` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

One class-based view, `PreferencesView` in `object_preferences/views.py`, and one template,
`object_preferences/preferences_form.html`. The view is a `DetailView` that builds one form per
preference group declared for the record's model, prefixed by the group's name, and on POST
validates all of them before applying each and saving once. It adds no access rule, so a project
composes Django's own mixins or decorators with it. Documentation goes in the README, story by
story. The example project gains accounts and two routed pages.

## Technical context

- Python 3.12+, Django 5.2 / 6.0 / 6.1, no dependency beyond Django (Article XII).
- Tests: pytest-django, factory-boy, from the shared bundle. No new development dependency.
- Templates: plain Django templates, linted by djlint through pre-commit.

## Constitution check

- **II/III Simplicity, anti-abstraction**: one view, one template, no base class or mixin of our
  own, no new setting.
- **V Security**: the template escapes everything through the template layer; the form posts with
  `{% csrf_token %}` and the view is `csrf_protect`ed; no access decision is made by the package
  (Article XII).
- **VI Documentation**: README and CHANGELOG in each story that adds public surface.
- **VIII Internationalisation**: template strings and the success message translatable; catalogue
  regenerated.
- **IX Data model**: the test app and the example gain a user model. Neither is packaged.
  `verbose_name` and `help_text` on the new `preferences` fields come from `PreferencesField`.
- **X Cohesion**: the behaviour is methods on the view.
- **XII Scope**: no default rule and no permission of our own.

## The view

```python
class PreferencesView(DetailView):
    template_name = "object_preferences/preferences_form.html"
    context_object_name = "record"
    success_url = None
    success_message = _("The preferences were saved.")

    def get_preferences(self) -> RecordPreferences:
        model = self.object._meta.model
        return getattr(self.object, registry.get_field(model).attname)

    def get_forms(self, data=None) -> dict[str, BaseForm]:
        preferences = self.get_preferences()
        return {
            name: preferences.get_form(name, data=data, prefix=name)
            for name in preferences
        }

    def get_context_data(self, **kwargs):
        if "forms" not in kwargs:
            kwargs["forms"] = self.get_forms()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        forms = self.get_forms(data=request.POST)
        if all([form.is_valid() for form in forms.values()]):
            return self.forms_valid(forms)
        return self.forms_invalid(forms)

    def forms_valid(self, forms):
        preferences = self.get_preferences()
        for name, form in forms.items():
            preferences.apply(name, form)
        preferences.save()
        messages.success(self.request, self.success_message, fail_silently=True)
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms):
        return self.render_to_response(self.get_context_data(forms=forms))

    def get_success_url(self) -> str:
        if self.success_url:
            return str(self.success_url)
        return self.request.path
```

The shape is the contract; names and docstrings follow the code-documentation standard. Notes:

- `get_preferences()` uses `_meta.model` so a `SimpleLazyObject` user works (research.md). A model
  without a `PreferencesField` raises `ImproperlyConfigured` from `registry.get_field()` on first
  use, naming the model (FR-018). GET reaches it through `get_context_data()`.
- `forms` maps each group name to its form, in registration order (FR-002, D7). The template uses
  the name for the legend.
- `forms_valid()` applies and saves once (N2, FR-004, FR-005). `save()` writes only the
  preferences (FR-010). A model with no groups saves an unchanged dictionary, which changes
  nothing.
- `get_success_url()` returns `request.path`, so the redirect lands on the same page (FR-008).
- No method does any work before `get()` or `post()`, so every Django access mixin or decorator
  refuses before the page reads a value or saves anything (FR-011, FR-012). A rule that tests the
  person against the record reads the record itself, in its own `test_func()`.
- `dispatch()` is wrapped in `csrf_protect` with `method_decorator`, as Django's own sign-in and
  password views are, so the page refuses a forged POST in a project without the CSRF middleware
  (D14).
- `context_object_name = "record"`. `DetailView` would otherwise name the record after its model,
  and for a user record that is `user`, which shadows the signed-in person from the
  authentication context processor. `record` is the glossary's word.

## The template

`object_preferences/templates/object_preferences/preferences_form.html`: a complete HTML document
(no `extends`, no `include`), `{% load i18n %}`, `lang` from `get_current_language`, a heading
naming the record, the `messages` list when present (`role="status"`), and a
`<form method="post">` with `{% csrf_token %}`, one `<fieldset>` per group with a `<legend>` of
the group name capitalised and `{{ form }}` inside, and a submit button. Every fixed string is
translated.

## Tests

`tests/test_views.py`, mirroring `object_preferences/views.py`, classes per subject
(`TestPreferencesView` and further classes as the stories need). Records through
`tests/factories.py`. Validation errors asserted by field and code. Messages asserted by level.
Markup assertions only for FR-015 (label for each control, a fieldset with a legend per group, the
error id referenced by the control's `aria-describedby`), found by id or role. No wording, no
layout.

Routes in `tests/urls.py`. Rule-composed views the routes need (a `UserPassesTestMixin` subclass,
the documented own-preferences view) live in `tests/testapp/views.py`, because they are host-
project code and the test app is the host project. The own-preferences view is the README
example verbatim (SC-006).

Settings: `tests/settings.py` gains `django.contrib.messages`, the session, authentication and
messages middleware, and `AUTH_USER_MODEL = "testapp.User"` (Story 2).

## Documentation

README gains "The preferences page", built per story:

- Story 1: routing the page for a model (`PreferencesView`), what it shows and saves, all or
  nothing, the redirect and `success_url`, the success message, the template name to override.
- Story 2: the warning that a page routed with no rule is open to anyone who can reach it
  (FR-019), and one example each of `LoginRequiredMixin`, `PermissionRequiredMixin`,
  `UserPassesTestMixin` against the record, and `get_queryset()` to limit the records; the error
  for a model without preferences.
- Story 3: "A page for each person's own preferences": the `get_object()` returning
  `self.request.user` example with `LoginRequiredMixin` (FR-014).

CHANGELOG under Unreleased. `CONTEXT.md` gains **preferences page** (D10). The English catalogue
is regenerated in Story 1. The example project's README section is rewritten in Story 3.

## The example project

- `example.User(AbstractUser)` with a unique `email` as `USERNAME_FIELD`, a `PreferencesField`,
  `verbose_name` and `help_text` on its new fields; `AUTH_USER_MODEL = "example.User"`.
- Two groups for `User` in `example/preferences.py`.
- Settings: auth, sessions and messages apps; their middleware and context processors;
  `LOGIN_URL`/`LOGIN_REDIRECT_URL`.
- URLs: `accounts/` from `django.contrib.auth.urls` with a plain `registration/login.html`;
  `projects/<pk>/preferences/` for `Project` behind `PermissionRequiredMixin`
  (`example.change_project`); `preferences/` for the signed-in person, as the README shows.
- The project list links to each project's page and to the person's own page, and shows who is
  signed in with a sign-out button.
- `seed_example` also creates `regular.user`, `regular.user2`, `staff.user` (with
  `change_project`) and `super.user`, all `password`, and gives `regular.user2` a stored value.
- One new example migration.

## Migrations

`tests/testapp/migrations/0002_*.py` (the test user) and `example/migrations/0002_*.py` (the
example user), each one file at S5.

## Risks

- A host project's own base template is not used by the package's template. That is the R4
  boundary, and overriding the template is the documented route.
