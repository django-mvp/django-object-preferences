# Feature Specification: Declare preferences for a model and read them from its records

**Feature Branch**: `001-declare-and-read-preferences`

**Created**: 2026-10-15

**Status**: Draft

**Serves**: G1, G2, G3 (roadmap item R1)

**Input**: Issue #7. A host project turns preferences on for any model it owns with a single
migration. After that, any installed app can declare its own named preference group for that model
with an ordinary Django form, and read the preferences back from any record without an extra
query. A preference nobody has changed reads its current default. A stored value that no longer
fits falls back to the default rather than breaking anything. Code can change and save preferences
with the same validation a person would meet on a page.

## Clarifications

### Session 2026-10-15

- Q: Where does a preference's default come from when the declaring form field gives no initial
  value? → A: From the field itself. A field with an initial value defaults to it. A field without
  one defaults to the value the field produces for an empty input (for example, an unticked box
  for a checkbox, nothing for an optional text field).
- Q: When code changes one preference in a group, what happens to the group's other preferences?
  → A: They keep the values they had. A change names only the preferences it changes, and the whole
  group is validated with the declaring form, with the unchanged preferences taking their current
  values.
- Q: What happens when a change sets a preference to exactly its default? → A: Nothing is stored
  for it, and any value stored before is removed. The record then follows the default if it later
  changes.
- Q: What happens when a developer asks for a group or a preference that nobody declared? → A: It
  is an error at the point of the call. This is different from a stored value for something no
  longer declared, which is ignored without complaint.
- Q: Which kinds of form field can a preference be? → A: Any field whose value can be kept on the
  record and read back without a database lookup: text, numbers, booleans, choices and multiple
  choices, dates, times, decimals, durations, UUIDs and the like. Fields that refer to other
  records (model choice fields) or carry uploads (file fields) are refused when the group is
  declared, because reading them would need a query or storage the record does not hold.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer turns preferences on for a model (Priority: P1)

A developer working on a host project chooses a model it owns, such as its user model or a
project model, and turns preferences on for it. The cost is one migration on that model. From
then on, every record of that model can hold preferences, and the developer never writes another
migration because preferences were added, removed or changed.

**Why this priority**: nothing else in the package works until a model can carry preferences.

**Independent Test**: turn preferences on for a test model, run its migrations, create records,
and confirm that each record holds no stored values and that no table besides the model's own
was created.

**Acceptance Scenarios**:

1. **Given** a model in the host project without preferences, **When** the developer turns them
   on and makes migrations, **Then** exactly one migration is produced, and it changes only that
   model.
2. **Given** a model that carries preferences, **When** records are created or already exist,
   **Then** each record holds no stored values until somebody changes a preference.
3. **Given** a model that carries preferences, **When** a preference group for it is declared,
   changed or removed, **Then** making migrations produces nothing.

---

### User Story 2 - A developer declares a preference group and reads it from a record (Priority: P1)

A developer writing an installed app declares a preference group for a model that carries
preferences. The group has a name and is an ordinary Django form, and each field is one
preference with its type, validation and default. The group is registered against the model in
the same way a model admin is registered, inside the app, and the package finds it without the
host project listing it anywhere. The developer then reads any preference in the group from a
record they already have in hand.

**Why this priority**: declaring and reading is the core of the package (G1, G2). The other
stories change or protect what this one reads.

**Independent Test**: declare a group in a test app, load a record, read each preference, and
assert the values and that the reads made no database queries.

**Acceptance Scenarios**:

1. **Given** an installed app that declares a group for a model, **When** the project starts,
   **Then** the group is known for that model without the host project naming it in its
   settings or code.
2. **Given** a record that has never changed a preference, **When** a developer reads it, **Then**
   it reads as the default the declaring field gives.
3. **Given** a record that has changed a preference, **When** a developer reads it, **Then** it
   reads as the stored value, as the type the declaring field produces (a date reads as a date,
   a decimal as a decimal).
4. **Given** a record already loaded, **When** a developer reads any number of preferences from
   any number of its groups, **Then** no database query is made.
5. **Given** records that never changed a preference, **When** the developer changes that
   preference's default in the declaring form, **Then** every one of those records reads the new
   default, and records that stored their own value still read it.
6. **Given** a group, **When** a developer asks a record for a preference or a group that was
   never declared for its model, **Then** the call fails with an error naming what was asked for.
7. **Given** a model with preferences turned on, **When** a developer asks which groups are
   declared for it, **Then** they get every declared group with its name and form.

---

### User Story 3 - A developer changes and saves a record's preferences from code (Priority: P2)

A developer changes one or more preferences of a record from code, for example in a data import,
a management command or a signal handler. The change is validated by the group's declaring form,
exactly as it would be if a person had submitted it on a page, and saved to the record.

**Why this priority**: preferences are read far more often than they are changed, and the
editing page (a separate feature) is the main way people change them. Code still needs a
supported way to write, and the page will be built on the same rules.

**Independent Test**: change preferences on a test record through the package, reload the record
from the database, and read the values back. Submit invalid input and confirm nothing changed.

**Acceptance Scenarios**:

1. **Given** a record, **When** a developer changes a preference to a valid value and saves,
   **Then** reloading the record reads the new value.
2. **Given** a record, **When** a developer changes one preference in a group, **Then** the
   group's other preferences keep the values they had.
3. **Given** a record, **When** a developer submits a value the declaring form rejects, **Then**
   the change fails with the form's validation error for that preference, and nothing on the
   record changes.
4. **Given** a record with a stored value, **When** a developer changes the preference back to
   its default, **Then** nothing is stored for it any more, and a later change to the default
   reaches this record.
5. **Given** a record with unsaved changes to its other fields, **When** a developer saves its
   preferences, **Then** only the preferences are written, and the other unsaved changes stay
   unsaved.
6. **Given** a record with stored values in two groups, **When** a developer saves one group,
   **Then** the other group's stored values are unchanged.

---

### User Story 4 - A developer changes a declaration without breaking existing records (Priority: P2)

A developer removes a preference, renames it, removes a whole group, or tightens a preference's
validation (narrows its choices, lowers a maximum, changes its type). Records saved under the
old declaration keep whatever they stored. Nothing raises when those records are read: values
that no longer fit are replaced by the current default, and values for things no longer declared
are ignored.

**Why this priority**: declarations change as apps evolve, and the package promises no
migrations for them (G1, G3). Without this, every change to a form would risk breaking pages.

**Independent Test**: store values on a record, change the declaring form so some of them no
longer fit, and read every preference without an error.

**Acceptance Scenarios**:

1. **Given** a record with a stored value that the current declaration rejects, **When** a
   developer reads that preference, **Then** it reads as the current default, and no error is
   raised.
2. **Given** a record with a stored value for a preference that is no longer declared, **When** a
   developer reads the group, **Then** the value is ignored, and every declared preference reads
   normally.
3. **Given** a record with stored values for a group that is no longer declared, **When** a
   developer reads the record's preferences, **Then** those values are ignored, and no error is
   raised.
4. **Given** a record whose stored data for a group is not in a shape the package wrote (for
   example, edited by hand in the database), **When** a developer reads that group, **Then** every
   preference that cannot be read reads as its default, and no error is raised.
5. **Given** a record with a stale stored value, **When** a developer saves that group with a
   valid change, **Then** the stale values for that group are gone from the record afterwards.

---

### Edge Cases

- Two installed apps declare a group with the same name for the same model: the project refuses
  to start, with an error naming the model, the group name and both declarations.
- An app declares a group for a model that has not turned preferences on: the project refuses to
  start, with an error naming the model and the group.
- A group's form contains a field that refers to other records or carries uploads: the project
  refuses to start, with an error naming the group and the field.
- A form's own cross-field validation (its `clean()` method) rejects a combination of values:
  a change from code fails with that error, as it would on a page. When reading, each preference
  is checked on its own, so a stored combination that the form now rejects still reads value by
  value.
- A group is declared for a parent model: it applies to that model only. Reaching models that
  inherit from it is a later feature.
- A record not yet saved to the database: preferences read their defaults, and changes can be
  made, but saving them needs the record to exist.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A host project MUST be able to turn preferences on for any model it owns, at the
  cost of one migration on that model and no table of its own. *(US1)*
- **FR-002**: All of a record's preferences MUST be kept on the record itself, and only stored
  values (preferences changed away from their default) MUST be written there. *(US1, US3)*
- **FR-003**: Declaring, changing or removing a preference group MUST NOT need a migration. *(US1)*
- **FR-004**: An installed app MUST be able to declare a named preference group for a model with
  an ordinary Django form, registered against the model in the way a model admin is registered.
  *(US2)*
- **FR-005**: The package MUST find every group declared by an installed app without the host
  project listing it. *(US2)*
- **FR-006**: Reading a preference from a record already loaded MUST make no database query.
  *(US2)*
- **FR-007**: A preference with no stored value MUST read as its current default, taken from the
  declaring form's field (its initial value, or the value the field gives an empty input when it
  has none). *(US2)*
- **FR-008**: A stored value MUST read back as the type the declaring field produces. *(US2)*
- **FR-009**: Asking a record for a group or preference never declared for its model MUST fail
  with an error naming it. *(US2)*
- **FR-010**: A developer MUST be able to list the groups declared for a model. *(US2)*
- **FR-011**: A developer MUST be able to change one or more preferences of a record from code,
  validated by the group's declaring form, and save them. *(US3)*
- **FR-012**: A change MUST leave the group's unchanged preferences with the values they had. *(US3)*
- **FR-013**: A change that fails validation MUST raise the form's validation error and leave the
  record unchanged. *(US3)*
- **FR-014**: A preference changed to its default MUST have no stored value afterwards. *(US3)*
- **FR-015**: Saving preferences MUST write only the record's preferences, and saving one group
  MUST leave every other group's stored values as they were. *(US3)*
- **FR-016**: A stored value the current declaration rejects MUST read as the current default,
  without raising. *(US4)*
- **FR-017**: Stored values for preferences or groups no longer declared, and stored data in a
  shape the package did not write, MUST be ignored on read, without raising. *(US4)*
- **FR-018**: Saving a group MUST drop that group's stored values that are stale or no longer
  declared. *(US4)*
- **FR-019**: The project MUST refuse to start when two groups for one model share a name, when a
  group is declared for a model without preferences turned on, or when a group's form has a field
  that refers to other records or carries uploads. Each error names what is wrong and where. *(US2)*
- **FR-020**: The README MUST show a preference group declared, read and changed, and the
  repository MUST include a small example project doing the same. *(US2, US3)*

### Key Entities

- **Record**: one instance of a model that carries preferences. It holds its own stored values.
- **Preference group**: a named Django form declared by one installed app for one model. Its
  fields are its preferences.
- **Preference**: one field of a group's form, with its type, validation and default.
- **Default**: the value a preference reads for a record with nothing stored for it, taken from
  the declaring field.
- **Stored value**: a value saved on a record because a preference was changed away from its
  default.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the one migration that turns preferences on, a developer can add, change or
  remove any number of preferences and groups for that model with zero further migrations.
- **SC-002**: Reading any number of preferences from a loaded record makes zero database queries.
- **SC-003**: Changing a default in a declaring form changes what every record without a stored
  value reads, with no change to stored data.
- **SC-004**: No stored data, however stale or malformed, makes reading a declared preference
  raise.
- **SC-005**: A developer following the README can declare a group, read a preference from a
  record and change it from code, and the example project runs the same steps.

## Assumptions

- The host project owns the model it turns preferences on for. Packaged models it does not own
  are out of scope, because it cannot add a field or a migration to them.
- A group applies to the model it was declared for. Reaching models that inherit from it is
  roadmap item R3.
- No page, view, URL or permission check is part of this feature. The editing page is #8, and
  admin integration is roadmap item R5.
- Reading preferences is not a way to select records. Filtering or ordering records by a
  preference is out of scope (Constitution, Article XII).
- Two changes to one record's preferences saved at the same moment are not merged: the later
  save wins. This matches how Django saves a field and is noted as an open risk.
- The package keeps depending on Django alone.
