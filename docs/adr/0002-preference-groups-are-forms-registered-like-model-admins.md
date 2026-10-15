# ADR 0002 — Preference groups are forms, registered like model admins

**Status:** accepted

## Decision

A preference group is an ordinary Django `forms.Form`. Each of its fields is one preference, with
the field's type, validation, choices and initial value. An app registers the form against a
model under a name, with `@register(Model, name="...")` in its `preferences.py`, and the package
imports every installed app's `preferences.py` when the project starts, the way the admin imports
`admin.py`. The host project lists nothing.

A group belongs to exactly the model it was registered for. Registration refuses, and so stops
the project from starting: a second group with the same name on one model, a model without a
`PreferencesField`, and a form field that refers to other records, carries an upload or is
entered as several inputs.

Code changes preferences through the same form. `change()` binds the group's form to the current
values with the changes laid over them, and `apply()` takes any bound form of the group. Either
way the form's own validation decides, exactly as it would on a page.

## Why

A form field already carries everything a preference needs, so a separate declaration format
would duplicate Django. Registration and discovery modelled on the admin are patterns an
experienced Django developer already knows, which the package's scope names as the tie-breaker.

The refusals each stop a mistake that would otherwise surface later and somewhere else. Two apps
sharing a name would write into each other's group. A field that refers to another record would
need a query to read, and one entered as several inputs could never read its stored value back.

Validating changes from code with the form keeps one set of rules for code and for the editing
page built on it.

## Revisit if

Model inheritance (roadmap item R3) needs a group to reach child models. That changes what
"exactly the model it was registered for" means, and should be decided there.
