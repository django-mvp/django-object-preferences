# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
  Everything not yet released goes under [Unreleased], grouped by change type:
  Added, Changed, Deprecated, Removed, Fixed, Security. Prepare Release promotes
  that section to a version heading and dates it.

  Do NOT write a version heading by hand. Tag Release fires on any push to main
  that touches pyproject.toml, and the only thing stopping it cutting a release
  from that push is the absence of a `## [X.Y.Z]` section matching the version
  in pyproject.toml. Writing one here defeats that guard, and the repository
  ends up with a tag and a GitHub Release for a version nobody prepared.

  Write for someone deciding whether to upgrade. Say what changed for them and
  what they have to do about it, not which files moved.
-->

## [Unreleased]

### Added

- The package, generated and not yet doing anything.
- `PreferencesField`, the model field that turns preferences on for a model. A
  model carries it by adding the field and one migration, and a record stores
  an empty dictionary until a preference is changed. Reading the attribute
  returns a `RecordPreferences` for that record.
- The English message catalogue.
- Preference groups: a group is a Django form registered for a model with
  `register` or `registry.register()`, in a `preferences.py` module that the
  package finds in every installed app at startup. `registry.get_groups()`,
  `registry.get_group()` and `registry.get_field()` look groups and the model's
  field up. Startup stops with a clear error for a duplicate name, a model
  without `PreferencesField`, or a form with a model choice, file or
  multi-value field.
- Reading preferences: `record.preferences["group"]["name"]` returns the
  stored value as the field's type, or the field's default, with no database
  query.
- Changing preferences from code: `record.preferences.change("group", name=value)`
  validates the values with the group's form and keeps the group's other
  preferences, and `record.preferences.save()` writes only the preferences.
  `get_form()` and `apply()` do the same for a whole submitted form. A value
  changed back to its default is no longer stored, and a value the form
  rejects raises a `ValidationError` and leaves the record as it was.
- An example project in `example/`, with a command that seeds it, showing a
  group declared, read and changed.
- Changing a declaration is safe for records that already stored preferences.
  A stored value that no longer fits reads the default, a stored preference or
  group that is no longer declared is ignored, and saving a group clears its
  stale values.
