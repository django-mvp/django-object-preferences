# Feature Specification: A page to change a record's preferences

**Feature Branch**: `002-preferences-page`

**Created**: 2026-10-15

**Status**: Draft

**Serves**: G4 (people can change a record's preferences on a page, while the host project
decides who has permission), G6 (works in any Django project without a user interface package)

**Roadmap**: R2

**Input**: Issue #8: "People need somewhere to change a record's preferences. Each record should
have a page listing every preference group declared for its model, saving changes with full
validation, in plain accessible markup that works in any Django project without a user interface
package. The host project decides where that page lives and who has permission to open it for a
given record, using Django's ordinary permission tools, and the documentation should show the
common case of pointing the page at the signed-in person so people can change their own
preferences."

## Builds on

FS-001 (#7) declares preference groups with Django forms, registers them for a model, stores and
reads them, supplies defaults, falls back to the default when a stored value no longer fits, and
lets code change preferences with validation. This page uses all of that and specifies none of it
again. What it needs from FS-001, in plain terms:

- a way to ask which preference groups are declared for a record's model, each with its name and
  its form
- a record's current value for every preference in a group, defaults included
- a way to change a record's preferences with the same validation a form gives, which saves only
  what that path saves

## Clarifications

### Session 2026-10-15

- Q: Does the page save one group at a time or every group together? → A: Every group together,
  with one save. If any group has an invalid value, nothing is saved and every group's errors are
  shown at once.
- Q: When the host project sets no access rule, who can open the page? → A: The page adds no rule
  of its own, exactly like Django's own editing views. The host project adds one with Django's
  ordinary permission tools, and the documentation says plainly that a page with none is open to
  anyone who can reach its address.
- Q: Where does a person end up after saving? → A: Back on the same page, showing what was saved,
  with a confirmation when the host project has Django's messages framework enabled. The host
  project can send them somewhere else instead.
- Q: Two groups declare a preference with the same name. Can they clash on the page? → A: No.
  Each preference on the page belongs to its group, and a value entered in one group never reaches
  the other.
- Q: Which groups appear: only those declared directly on the model, or any that reach it some
  other way? → A: Every group FS-001 reports as declared for the record's model. When later work
  lets groups reach a model through inheritance, the page shows those too without change.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A user changes a record's preferences on its page (Priority: P1)

A user who has been allowed onto a record's preferences page sees every preference group declared
for that record's model, each preference showing its current value. They change some values and
save. Valid changes are kept. If anything they entered is invalid, nothing is saved and they are
told which preference is wrong, with what they typed still in place.

**Why this priority**: This is the feature. Without it, preferences can only be changed from code.

**Independent Test**: Declare two preference groups for a test model, route the page for that
model with no access rule, open it for one record, submit changed values and read the record back.

**Acceptance Scenarios**:

1. **Given** a model with two preference groups declared, **When** a user opens the page for one
   of its records, **Then** the page shows a control for every preference in both groups.
2. **Given** a record that has changed one preference and left the rest alone, **When** a user
   opens its page, **Then** the changed preference shows its stored value and every other
   preference shows its current default.
3. **Given** a record whose stored value for a preference no longer fits that preference's
   declaration, **When** a user opens its page, **Then** the page opens and that preference shows
   its current default.
4. **Given** a user on a record's page, **When** they change preferences in two groups and save,
   **Then** both changes are kept on the record and they are returned to the page showing the
   saved values.
5. **Given** a user on a record's page, **When** they enter an invalid value in one group and a
   valid change in another and save, **Then** nothing is saved, the page shows an error attached
   to the invalid preference, and both entered values are still in place.
6. **Given** a record with no stored values, **When** a user saves its page without changing
   anything, **Then** the record still has no stored values.
7. **Given** two groups that each declare a preference with the same name, **When** a user enters
   a different value for each and saves, **Then** each group keeps its own value.
8. **Given** a host project with Django's messages framework enabled, **When** a user saves valid
   changes, **Then** a success message is added.
9. **Given** a record with other fields besides its preferences, **When** a user saves its page,
   **Then** none of those other fields is written.

---

### User Story 2 - A developer adds the page to a project and decides who may use it (Priority: P1)

A developer adds the preferences page for one of their models to the project's URLs, wherever
suits the project. They decide who may open it for a given record using Django's ordinary
permission tools: requiring a signed-in person, requiring a permission, testing the person against
the record, or limiting which records the page will look up. Anyone else is refused in Django's
usual way and the record is left untouched.

**Why this priority**: Without this the page cannot be put in a project safely. It is half of G4,
and P1 alongside Story 1 because neither is usable alone.

**Independent Test**: Route the page for a test model with an access rule that admits only the
record's owner. Open and submit it as the owner, as another signed-in person and as an anonymous
visitor, and check what each one gets and what is saved.

**Acceptance Scenarios**:

1. **Given** a page routed to require a signed-in person, **When** an anonymous visitor opens it,
   **Then** they are sent to the project's sign-in page and nothing about the record is shown.
2. **Given** a page whose access rule refuses a signed-in person for a record, **When** that
   person opens it, **Then** they are refused and nothing about the record's preferences is shown.
3. **Given** a page whose access rule refuses a person for a record, **When** that person submits
   values to it directly, **Then** they are refused and the record's preferences are unchanged.
4. **Given** a page that limits which records it will look up, **When** a person asks for a record
   outside that set, **Then** the page responds as for a record that does not exist.
5. **Given** a page routed for a model, **When** a person asks for a record that does not exist,
   **Then** the page responds that it was not found.
6. **Given** a host project whose installed apps hold Django's own apps and this package and
   nothing else, **When** a developer routes the page, **Then** it opens and saves with the
   package's own template.
7. **Given** a developer routes the page for a model that has not been given preferences, **When**
   the page is first used, **Then** it fails with an error telling the developer the model has no
   preferences.

---

### User Story 3 - A developer gives each signed-in person a page for their own preferences (Priority: P2)

A developer whose user model carries preferences points the page at whoever is signed in, so
every person can change their own preferences at one address with no record identifier in it.
The documentation shows exactly how, as the common case.

**Why this priority**: It is the most common use and the issue asks for it by name, but it is a
way of using Story 2's page rather than a separate capability, so it comes after the page exists.

**Independent Test**: Follow the documented example in a test project, sign in as two different
people in turn, and check each one sees and changes only their own preferences.

**Acceptance Scenarios**:

1. **Given** a page set up as the documentation shows for the signed-in person, **When** a
   signed-in person opens it, **Then** it shows their own preferences.
2. **Given** that page, **When** a signed-in person saves a change, **Then** the change is kept on
   their own record and no other person's record changes.
3. **Given** that page, **When** an anonymous visitor opens it, **Then** they are sent to the
   project's sign-in page.

---

### Edge Cases

- A model with preferences turned on but no groups declared: the page opens, shows no controls,
  and saving it changes nothing.
- A record whose stored values include a preference that no longer exists: the page opens and
  shows only the preferences that are declared. What happens to the stale value on save follows
  FS-001's rules for changing preferences from code. The page adds no rule of its own.
- A group whose form needs a value the person left empty: the error is shown against that
  preference like any other invalid value.
- Two people saving the same record's page at nearly the same time: the later save wins. The page
  does not merge their changes.
- A host project that wants different markup replaces the package's template in the usual Django
  way. Named places for a user interface package to restyle are later work (R4).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST provide a page that edits the preferences of one record, which a
  host project adds to its own URLs. The package MUST NOT add it to any URL by itself.
- **FR-002**: The page MUST show every preference group FS-001 reports as declared for the record's
  model, with a control for every preference in each.
- **FR-003**: Each control MUST start from the record's current value: its stored value where it
  has one that fits, and the preference's current default otherwise.
- **FR-004**: Saving MUST validate every group with its own declaring form and save through the
  same path FS-001 gives code for changing preferences, so a page and code apply the same rules.
- **FR-005**: Saving MUST be all or nothing across the page: if any group is invalid, no group's
  changes are saved.
- **FR-006**: When saving fails, the page MUST show each error against the preference it belongs
  to, or against its group when it belongs to no single preference, and MUST keep every value the
  person entered.
- **FR-007**: Preferences from different groups MUST be kept apart on the page even when they
  share a name.
- **FR-008**: After a successful save the page MUST send the person back to itself by default, and
  the host project MUST be able to choose a different destination.
- **FR-009**: After a successful save the page MUST add a success message when Django's messages
  framework is enabled, and MUST work without it when it is not.
- **FR-010**: Saving MUST write the record's preferences and nothing else on the record.
- **FR-011**: The page MUST apply no access rule of its own. The host project MUST be able to
  decide who may open and submit it for a given record with Django's ordinary permission tools,
  including limiting which records it will look up.
- **FR-012**: A refused or anonymous request MUST receive Django's usual response for the rule
  that refused it, and MUST neither reveal nor change the record's preferences.
- **FR-013**: A request for a record that does not exist, or that the page will not look up, MUST
  receive a not-found response.
- **FR-014**: The host project MUST be able to point the page at the signed-in person's own
  record, and the documentation MUST show how, as a working example.
- **FR-015**: The page's markup MUST give every preference control an accessible label, present
  each group as a labelled group of controls, and associate each error with the control it
  concerns.
- **FR-016**: The page MUST render and save with the package's own template in a project that has
  no user interface package installed, and the package MUST NOT depend on one.
- **FR-017**: Every piece of text the page itself shows MUST be translatable.
- **FR-018**: Using the page for a model that has not been given preferences MUST fail with an
  error that names the problem for the developer.
- **FR-019**: The documentation MUST say that a page routed with no access rule is open to anyone
  who can reach its address, and show how to add one.

### Key Entities

- **Preferences page**: the page that edits one record's preferences. It shows every preference
  group declared for the record's model and saves them together. Where it lives and who may use
  it are the host project's to decide.
- **Record**, **Preference group**, **Preference**, **Default**, **Stored value**: as defined in
  `CONTEXT.md` and specified in FS-001.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer puts the page for one of their models into a project and restricts it
  with Django's ordinary permission tools without writing a form or a template of their own.
- **SC-002**: Every preference group declared for a record's model appears on its page, with none
  missing.
- **SC-003**: No invalid value is ever saved through the page, and every rejected value is
  reported against the preference it belongs to.
- **SC-004**: A person refused by the host project's access rule can neither see nor change the
  record's preferences, whether they open the page or submit to it directly.
- **SC-005**: The page works in a project with no user interface package installed.
- **SC-006**: The documentation's example of a page for the signed-in person's own preferences
  works as written.

## Assumptions

- FS-001 is delivered first. The page reads groups, values and defaults through it and saves
  through it. It does not touch storage itself.
- Who may change a record's preferences is always the host project's decision (constitution,
  Article XII), so the package ships no default rule and no permission of its own.
- The host project decides the page's address. The package may document a typical address but
  installs none.
- A host project can already change the page's markup by overriding its template the ordinary
  Django way. Documented restyling points for a user interface package are R4, and the Django
  admin is R5. Both are out of scope here.
- The page shows every declared group. Choosing a subset of groups for one page is not part of
  this feature.
