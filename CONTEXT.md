# django-object-preferences

Domain vocabulary for django-object-preferences. The terms below are the ones
to use in issues, commits and tests.

## Core concepts

**Host project**:
The Django project that installs this package. It owns its models, its URLs and
the decision about who may change a record's preferences.
_Avoid_: consumer, client, downstream, user (a user is a person using the host
project, not the project itself).

**Record**:
One instance of a model that carries preferences: a person, when the model is
the user model, or something like a project or a dataset.
_Avoid_: object (except in Django's own names such as `get_object()`), instance,
entity.

**Preference**:
One named value a person can change for a record, such as a theme or whether a
page shows a section. It has a default, and a record that has never changed it
holds nothing for it.
_Avoid_: setting (Django settings are site-wide and live in code), option,
config.

**Preference group**:
A set of related preferences that one installed app declares for one model,
under a name of its own. A group is declared with a Django form, and the form's
fields are its preferences.
_Avoid_: namespace, section, category, schema.

**Preferences page**:
The page where a person changes a record's preferences. It shows every
preference group declared for the record's model and saves them together or not
at all. A host project routes it and decides who may use it.
_Avoid_: settings page, profile page, preferences form.

**Default**:
The value a preference has for every record that has not changed it. It comes
from the declaring form's field, never from what is stored.

**Stored value**:
A value saved on a record because someone changed a preference away from its
default. Only stored values are written to the record.
_Avoid_: override.

## Terms deliberately not used

**Settings**: implies Django's `settings` module, which is site-wide and fixed
when the process starts. Preferences belong to one record and change at runtime.

**Config** or **configuration**: already taken by the configuration dictionaries
of packages a host project is likely to run alongside this one, and it suggests
something a developer edits rather than something a person chooses.

**Profile**: suggests a model of its own joined to the user. Preferences live on
the record itself, and the record need not be a person.

**Schema**: suggests a separate declaration format such as JSON Schema. A
preference group is declared with an ordinary Django form.
