# ADR 0005 — A value JSON cannot encode is stored as its text

**Status:** accepted

## Decision

A preference's cleaned value is stored as the record's preferences field's JSON encoder writes it.
When the encoder cannot serialize the value, the value is stored as its text instead: `str()` of
what the field prepares for its widget, which is the text the form shows and submits. Reading
cleans that text with the field, as it cleans every stored value (ADR 0001), so the value reads back
as the type its field produces. A `zoneinfo.ZoneInfo` from a timezone field is stored as its key,
`"Europe/Berlin"`, and reads back as the same `ZoneInfo`.

The text is only stored when the field cleans it back to a value equal to the one being stored.
Otherwise saving raises a `TypeError` that names the field and the value, so a value is never
written that would silently read as the default.

Whether a value is stored at all is decided on the cleaned values, before either form of encoding,
so a value left at its default stores nothing, whatever its type.

## Why

The package reads every stored value through its field's `clean()` (ADR 0001), so any text the
field accepts is already a faithful way to store a value. The text a form submits is the one
representation every form field is built to accept, and a `JSONField` preference is already stored
this way. Storing it needs no encoder of the host's, no registry of types and nothing from the
field's author.

The alternatives each ask for more: a custom encoder handles only the types someone listed and
still needs a decoder that knows which type to rebuild, and pickling stores something a person
cannot read in the database and that breaks when a class moves.

Checking that the text cleans back before storing it keeps the failure where the mistake is. A
field that cannot be stored either way fails when a developer first saves it, rather than reading
the default for every record afterwards.

## Revisit if

A common field type's own `clean()` stops accepting the text its widget shows, so that the
`TypeError` on save becomes something developers meet routinely rather than for an unusual field.
