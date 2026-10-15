# Decisions — 001, declare preferences for a model and read them from its records

Rationale behind the specification that is too long to carry inside it, plus every point settled
without asking the repository owner. The owner handed this specification over on 2026-10-15, so
the reading of the issue below was written and treated as confirmed rather than put to them. Each
decision is one they can veto at review. The specification stands alone. This file records why it
reads the way it does.

The design direction comes from the "Conclusions so far" in `docs/brainstorm.md`, which were
written before any specification and are not ratified. Each one this feature depends on is
settled here.

## The reading of the issue

A developer working on a host project turns preferences on for a model it owns with one
migration. A developer writing any installed app then declares a named preference group for that
model with an ordinary Django form, registered the way a model admin is, and reads the preferences
from any record already loaded without a query. Unchanged preferences read their current default,
stored values that no longer fit fall back to the default, and code can change and save
preferences with the form's own validation. The editing page and permissions belong to #8.
Inheritance belongs to R3 and admin integration to R5. The README and a small example project
show the whole thing.

## One field on the record holds only stored values

**Decided**: every preference of a record is kept in one field on the record, holding only the
values changed away from their default, grouped by preference group.

**Why**: this is what makes G1 and G2 hold together. The field is added once, so any app can
declare preferences later with no migration of its own (G1). The values arrive with the record,
so reading them needs no query (G2). Keeping only changed values means the default lives in the
form, so changing it reaches every record still on it (G3). Mastodon moved to the same shape in
production. A row per preference would cost a query per read, and a column per preference would
cost a migration per preference, which is the problem the package exists to remove.

## A group is a Django form, registered like a model admin

**Decided**: a preference group is an ordinary `forms.Form`. Its fields are its preferences. It is
registered against a model, under a name, in the way `admin.register` registers a model admin,
and the package discovers registrations in installed apps in the way the admin discovers
`admin.py` modules.

**Why**: a form field already carries a type, validation, choices, a label and an initial value,
so a second declaration format would duplicate Django. The admin's register-and-autodiscover
pattern is the one an experienced Django developer already knows, which the README names as the
tie-breaker for close calls. The exact module name and call signature are planning decisions.

## Group names are unique per model, and clashes stop the project starting

**Decided**: two groups registered for the same model under the same name, a group registered for
a model that has not turned preferences on, and a form with an unsupported field all stop the
project from starting, with an error naming the problem.

**Why**: each is a developer mistake that would otherwise surface later as values silently
written into another app's group, or as a read that fails on a page. Failing at start-up puts the
error in front of the developer who caused it. Whether this is a system check or an exception at
registration is for planning.

## The default comes from the field

**Decided**: a preference's default is its field's initial value. A field with no initial value
defaults to whatever the field produces for an empty input.

**Why**: the brainstorm says defaults live in the declaring form, and the initial value is the
form's own notion of a starting value. The fallback avoids requiring every field to state one,
and matches what a person would get by submitting the form with that field left empty.

## Reads come back typed

**Decided**: a stored value reads back as the type its field produces, so a date reads as a date
and a decimal as a decimal.

**Why**: storing values loses Python types (a date becomes text). Running the stored value back
through the field on read restores them and doubles as the staleness check, so one mechanism
serves both FR-008 and FR-016.

## Fields that refer to other records or carry uploads are refused

**Decided**: model choice fields and file fields cannot be preferences in this feature.

**Why**: reading a model choice field means looking the other record up, which breaks G2. A file
needs storage the record does not hold. The README's scope already says a choice that relates two
records needs a model of its own. Both can be revisited in a later feature if a real need appears.

## Unknown keys are ignored, stale values fall back

**Decided**: on read, values for preferences or groups no longer declared are ignored, values the
current field rejects read as the default, and stored data in a shape the package did not write
is treated as absent. Nothing raises.

**Why**: this is G3 stated directly, and it is what lets a developer change a form without a data
migration. Raising on a stale value would turn a routine form change into a broken page for every
record that ever stored the old value.

## Saving a group cleans that group only

**Decided**: saving a group rewrites that group's stored values from the validated form, so stale
or undeclared values within it disappear. Other groups, including groups no longer declared, are
left exactly as they are.

**Why**: a save validates the whole group, so it is the natural moment to drop what no longer
fits. Touching other groups would let one app's save change another app's data. Values for a
removed group are left in place because they are harmless and ignored, and deleting another
app's data without being asked is worse than leaving it.

## A change names only what it changes

**Decided**: changing preferences from code names only the preferences being changed. The group
is validated with the form, with unchanged preferences taking their current values, so
cross-field validation still sees the whole group.

**Why**: requiring every preference on every change would make code callers repeat values they
do not care about, and would make it easy to reset a preference by forgetting it. Filling in the
current values keeps the form's validation identical to a page submission.

## Changing back to the default removes the stored value

**Decided**: a preference changed to a value equal to its default has nothing stored afterwards.

**Why**: storing it would freeze the record on today's default, and a later change to the
default would not reach it. That would break the promise in G3 for anyone who once set the value
back by hand.

## Asking for something undeclared is an error

**Decided**: reading a group or preference that was never declared for the record's model fails
with an error naming it.

**Why**: this is a typo in code, not a data problem. Silently returning nothing would hide the
mistake. Stale stored data is the opposite case and is ignored, because no developer wrote it in
the code being run.

## Saving preferences writes only the preferences

**Decided**: saving preferences writes the record's preferences and nothing else.

**Why**: a developer saving preferences in a signal handler or a request does not expect other
pending changes on the record to be written as a side effect. It also keeps the write small.

## Inheritance, the page and the admin are out of scope

**Decided**: a group applies to the model it was declared for. The editing page, its views, URLs
and permissions are #8. Reaching child models is R3. The admin is R5.

**Why**: the issue's boundary and the roadmap's say so. Settling now that a group applies to one
model keeps R3 free to choose how inheritance works.

## Open risk: concurrent saves

Two saves of the same record's preferences at the same moment are not merged, and the later one
wins, even when they change different groups. This is how saving any Django field behaves. It is
left as a risk rather than a requirement because preferences change rarely and usually by the
person the record belongs to. Planning may choose a cheap guard if one exists.

## Decisions made while planning

The plan was reviewed once before any code was written. Its verdict was to approve, with one
medium and four low findings. Each one below was applied to the plan. None changes a
requirement.

## D1 — Fields entered as several inputs are refused, alongside related-record and upload fields

**Decision**: registering a group whose form has a `forms.MultiValueField`, such as
`SplitDateTimeField`, fails at start-up with the same kind of error as a model choice field or a
file field. The form's fields are read from an instance of the form, so a field added in its
`__init__` is checked too.

**Why**: such a field takes its value as a list of inputs (`when_0`, `when_1`) and cleans it from
a list. A value stored on the record would never clean back, so it would always read as the
default. Worse, a change to another preference in the same group would bind the form with that
value under the wrong key and silently drop it. Refusing it at start-up puts the error in front of
the developer. The spec's examples of supported fields (text, numbers, booleans, choices, dates,
times, decimals, durations, UUIDs) are all single-input fields, and a date and a time can each be
a preference of their own.

**Revisit if**: someone needs a combined date and time preference. A `DateTimeField` already
covers it with one input.

**ADR:** none — a narrowing of which form fields are accepted, recorded in the README and in the
error itself

## D2 — Values are stored as the form field would render them

**Decision**: a changed value is stored as the field's `prepare_value()` gives it, then encoded
with `DjangoJSONEncoder`. A change from code binds the form with the same rendering of each current
value.

**Why**: reading a value back runs it through the field's `clean()`, which takes a value in the
shape a form submission has. For most fields that is the value itself. For `forms.JSONField` it is
JSON text: a string value stored as-is would be parsed as JSON on read and fall back to the
default. `prepare_value()` is the field's own answer to "what does my value look like as form
data", so using it keeps one rule for every field instead of a special case.

**Revisit if**: a field's `prepare_value()` turns out to return something that is not valid input
to its own `clean()`.

**ADR:** none — an internal detail of how values are stored, invisible to a host project

## D3 — The group name is positional-only

**Decision**: `change(name, /, **values)` and `get_form(name, /, data=None, **kwargs)`.

**Why**: without it, a preference called `name` cannot be changed, because the keyword binds to
the group parameter and Python raises `TypeError`. Any field name is a valid preference name.

**Revisit if**: never, short of a change to Python.

**ADR:** none — a signature detail visible in the API documentation

## D4 — The registry finds a model's preferences field

**Decision**: `PreferenceRegistry.get_field(model)` returns the model's `PreferencesField` and
raises `ImproperlyConfigured` when the model has none or more than one. Registration uses it.

**Why**: the check had to exist for registration anyway. Naming it gives the editing page (FS-002)
one way to find the field, whatever the host called it, and to refuse a model without
preferences, instead of repeating the scan. Two preferences fields on one model would give two
accessors over the same groups with separate storage, which no host means to set up.

**Revisit if**: a real need for two separate sets of groups on one model appears.

**ADR:** none — follows from the registration design already recorded above

## D5 — The package ships an English catalogue

**Decision**: `object_preferences/locale/en/LC_MESSAGES/django.po` is generated with
`makemessages` and ships with the package.

**Why**: Constitution Article VIII. The field's `verbose_name` and `help_text` are user-facing
wherever a host shows its model's fields.

**Revisit if**: the package stops carrying user-facing strings.

**ADR:** none — required by the constitution, nothing to decide

## Design review watch items

Carried into the implementation briefs rather than re-planned:

- The `preference_registry` fixture copies each inner dictionary, so one test's registration
  cannot leak into the next.
- A required field with no initial value reads as empty and makes every change to its group fail
  until it is given a value. That is how the form behaves on a page too. The README says so in one
  sentence.
- The example project's settings carry a development-only secret key and `ALLOWED_HOSTS = ["*"]`,
  each with a comment saying it only ever runs locally.
- Messages raised for developer mistakes (`ImproperlyConfigured`, `KeyError`) are not translated.
  Article VIII covers user-facing strings, and these are developer-facing.

## D6 — Stories are dispatched in-turn while gateway spawning is unavailable

**Decision**: each story's implementer runs as an in-turn agent on the Sonnet tier, in its own
worktree, with the usual brief, craft-skill gate, receipts check and independent re-verification.

**Why**: on 2026-10-15 the gateway refused every subagent spawn from this session ("the selected
account or native runtime is unavailable"), for every model. The orchestrating session was told.
Running the implementers in-turn keeps the work on the tier the pipeline sets for it and keeps the
builder separate from the one who accepts the story. What it loses is the per-story cost
attribution, because the transcripts land with this session rather than under each worktree.

**Revisit if**: spawning works again, at which point the remaining stories go back to it.

**ADR:** none — a one-off workaround for a tooling outage, nothing in the package

## D7 — Where preferences are stored, and how they are read

**Decision**: the spec's decisions on storage ("One field on the record holds only stored values",
"The default comes from the field", "Reads come back typed", "Unknown keys are ignored, stale
values fall back") together with the accessor design in `research.md` §2 are one standing rule
for the package.

**Why**: every later feature reads and writes through it, and a reasonable engineer would ask why
preferences are not columns or rows.

**Revisit if**: preferences need to be queryable, which the constitution rules out.

**ADR:** docs/adr/0001-preferences-are-stored-on-the-record.md

## D8 — How preference groups are declared

**Decision**: the spec's decisions "A group is a Django form, registered like a model admin" and
"Group names are unique per model, and clashes stop the project starting", with D1 and D3, are one
standing rule for how apps declare preferences.

**Why**: it is the package's public interface for every app that declares preferences, and FS-002
and later features build on it.

**Revisit if**: model inheritance (R3) changes which model a group applies to.

**ADR:** docs/adr/0002-preference-groups-are-forms-registered-like-model-admins.md
