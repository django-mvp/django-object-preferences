# ADR 0001 — Preferences are stored on the record, and only when changed

**Status:** accepted

## Decision

A record's preferences live in one field on the record itself, `PreferencesField`, a subclass of
Django's `JSONField`. A host project adds that field once, and that is the only migration
preferences ever cost it. The field holds only stored values: the preferences someone changed
away from their default, grouped by preference group. A default is never stored. It is read from
the declaring form every time.

Reading goes through the declaring form's fields. A stored value is passed through its field's
`clean()`, which gives it back its type and checks it against the current declaration in the same
step. Whatever is stored, a read never raises: a value that no longer fits reads as the current
default, and anything not declared, or not in a shape the package writes, is ignored. Asking for
a group or preference that was never declared is still an error, because that is a mistake in
code rather than old data.

`record.preferences` returns an accessor around the record, the way a `FileField` returns a
`FieldFile`, so reading never needs a query.

## Why

The package exists so that any installed app can add preferences to a model without a model, a
table or a migration of its own, and so that reading them costs nothing. A column per preference
costs a migration per preference. A row per preference costs a query per read and loses the
value's type. One JSON field on the record avoids both, and Mastodon moved its user settings to
the same shape in production.

Storing only changed values is what makes a default change reach every record still on it. A
stored copy of the default would freeze each record on the value of the day it was saved.

Reading through the form field turns one mechanism into both the type conversion and the
staleness check. Not raising is what lets a developer narrow a choice or remove a preference
without a data migration. Raising on a stale value would turn a routine form change into a
broken page for every record that ever stored the old value.

## Revisit if

A host project needs to filter or order records by a preference. That is out of scope by the
constitution (Article XII), and the answer then is a real column on the host's model, not a
query into this field.
