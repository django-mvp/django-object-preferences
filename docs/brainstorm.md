# Brainstorm

Working notes from before the first specification. Nothing here is a ratified
decision. Each one is settled in the feature specification that needs it.

## The problem

Many Django projects need a few settings per person: a theme, a language, a
time zone, whether a profile is public. Some also need settings per record,
such as how a project's or a dataset's pages behave. The usual answers each
cost something:

- A profile model joined one-to-one to the user. Every new setting is a column
  and a migration, and every app that wants a setting either edits that model or
  adds a profile model of its own, so a page that needs three apps' settings
  makes three joins.
- A key/value table, one row per setting. Any app can add settings, but reading
  a person's settings is a query of its own, and values lose their types.

The idea here is to keep every preference for a record in one JSON field on
that record, and to let each app declare its own group with a Django form.

## Prior art

| Project | How it stores preferences | What it shows |
|---|---|---|
| [Mastodon](https://github.com/mastodon/mastodon/blob/main/app/models/user_settings.rb) | One JSON column on the users table since 2023, moved from one row per setting. Keys, defaults and namespaces are declared in a `UserSettings` class | The single-column design, in production at scale |
| [Wagtail](https://github.com/wagtail/wagtail/blob/main/wagtail/users/models.py) | A one-to-one `UserProfile` with typed columns, plus one JSON field for dismissed hints | An application that owns its whole schema can afford columns |
| GitLab, Discourse, Zulip | A one-to-one table of typed columns | The same |
| WordPress, Drupal, Nextcloud | Key/value rows per user, namespaced by plugin | Plugins cannot add columns, so they share a namespaced store |
| VS Code | Only changed values are stored, and each extension declares its settings | Defaults live in code, and the settings page is generated from the declarations |
| [django-dynamic-preferences](https://github.com/agateblue/django-dynamic-preferences) | One row per preference per user, with a cache in front | Covers per-user and global settings, with its own type system beside Django forms. Last release 1.17.0, January 2025 |
| [django-entangled](https://github.com/jrief/django-entangled) | Edits keys of a JSON field through a ModelForm | Solves mixing JSON keys and model fields in one form. Maintained, last release 0.7, October 2025 |

Django itself keeps the chosen language in a cookie, and its time zone
documentation gives a middleware for projects to copy. It leaves storage and
the page to the project.

## Why another package

django-dynamic-preferences is the closest, and it also supports preferences
per model instance. It differs in two ways that matter here: it reads each
preference from its own table rather than from the record, and it declares
preferences with its own classes rather than with Django forms. Its dependency
on `persisting_theory` is pinned to one exact version.

django-entangled is narrower. It would save a little view code, but a form
declared for a group of preferences already edits that group on its own.

## Conclusions so far

- One JSON field per record, holding only the values a person has changed.
  Defaults live in the declaring form, so adding a preference never needs a
  migration and changing a default reaches everyone who never changed it.
- A group of preferences is declared with an ordinary Django form, registered
  against a model the way `admin.register` registers a model admin.
- Registration follows model inheritance, so a group declared for a parent model
  reaches its children.
- Unknown keys are ignored, and a stored value that no longer validates falls
  back to the default.
- The editing page is a class-based view that takes its record from
  `get_object()`. Who may edit a record is the host project's decision.
- Anything a project filters records by stays a column. A key path lookup on a
  JSON field misses every record still on the default, and Django's
  documentation warns that such lookups are not guaranteed to produce
  exhaustive sets.
