# ADR 0003 — The preferences page is a detail view with no access rule of its own

**Status:** accepted

## Decision

The page for changing a record's preferences is `PreferencesView`, a subclass of Django's
`DetailView`. It finds its record through `get_object()`, so a project points it at any record,
including the signed-in person with a `get_object()` that returns `self.request.user`, and limits
the records it opens with `queryset` or `get_queryset()`.

It shows one form per preference group, each prefixed with the group's name. On submit it
validates every group first, and only when all of them are valid does it apply each one and save
the record's preferences once. One invalid value means nothing is saved.

It applies no access rule. The package ships no URL, no default rule and no permission, and a
project restricts the page with Django's own access mixins and decorators. The view does no work
before `get()` and `post()`, so those tools refuse before the page reads or saves anything. It
does check the CSRF token itself, the way Django's sign-in views do.

## Why

Who may change a record's preferences depends on what the record is: a person's own settings, a
project only its members may change, a dataset only staff may touch. The package cannot know, so
any default it picked would be wrong for someone. A built-in "signed in only" default would also
surprise a developer, because Django's own editing views add no rule either. The cost is that a
page routed with no rule is open to anyone who can reach it, so the README says so where it shows
how to route the page.

`DetailView` already does the lookup, the not-found response and the template resolution, and
every Django developer knows how to restrict it. `UpdateView` was set aside because it builds one
model form for the record and would write every field that form holds. Saving every group
together, rather than one at a time, means a person is never left unsure which half of a
submission was kept.

## Revisit if

A user interface package needs to save one group at a time, or to show a subset of groups on one
page. Either is a different page built on the same forms, not a change to this one.
