# ADR 0004 — A preference group has a verbose name, given when it is registered

**Status:** accepted

## Decision

A preference group carries a `verbose_name`: what people see it called, such as the heading of
its part of a page. It is an optional argument to `registry.register()` and to the `register`
decorator, and it is stored on the `PreferenceGroup`. A project marks it for translation with
`gettext_lazy`, and the group keeps it lazy, so it is translated each time it is shown. When none
is given, the group is called by its name with the first letter capitalised.

The name stays the group's identifier: the key in `record.preferences`, the prefix of the page's
controls and the key the registry looks it up by. Only `verbose_name` is shown to people, by the
package's own page and by any page built on the package.

## Why

A name is an identifier, so it cannot be translated and often reads poorly as a heading. Django
already pairs an identifier with a translatable label everywhere a person sees one: a model's
`verbose_name`, an app's `AppConfig.verbose_name`, a form field's `label`. The same word, argument
and fallback make the group behave the way an experienced Django developer expects, which the
package's scope names as the tie-breaker.

It is given at registration rather than declared on the form, because the form is an ordinary
Django form (ADR 0002) and the same form may be registered for more than one model.

## Revisit if

A group needs text beyond its heading, such as a description, at which point the group's
display attributes should be decided together.
