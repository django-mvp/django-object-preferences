# Decisions for FS-002: A page to change a record's preferences

Decisions taken while specifying this feature, with the reason each one is defensible. Each can
be overruled at the specification review.

## D1. The reading of the issue, taken as agreed

**Reading.** A record gets one page, added to the host project's own URLs, that shows every
preference group declared for the record's model and saves changes with each group's own form
validation. The host project decides where it lives and who may use it with Django's ordinary
permission tools. The documentation shows the common case: a page for the signed-in person's own
preferences. The markup is plain and accessible and needs no user interface package.

**Boundary.** Declaring groups, storage, reading, defaults, the fallback for stale values and
changing preferences from code belong to FS-001 (#7). Restyling points for a user interface
package belong to R4 and the Django admin to R5. Inheritance between models is R3.

**Why.** It is the issue's own paragraph and R2's deliverables, with nothing added beyond the
points below.

**ADR:** none — the reading of the issue, recorded in the spec itself

## D2. One save for every group, all or nothing

**Ambiguous:** whether each group saves on its own or the page saves them together.

**Chosen:** one save for the whole page. If any group is invalid, nothing is saved and every error
is shown at once.

**Why:** the issue describes one page listing every group, and "saving changes with full
validation". One form submission that partly succeeds would leave a person unsure what was kept.
Separate saves per group would be a separate design that a user interface package can still build
on top later.

**ADR:** docs/adr/0003-the-preferences-page-is-a-detail-view-with-no-access-rule.md

## D3. The page applies no access rule of its own

**Ambiguous:** what happens when a host project routes the page without saying who may use it.

**Chosen:** nothing is added. The page behaves like Django's own editing views, and the host
project adds a rule with the usual tools: requiring a signed-in person, requiring a permission,
testing the person against the record, or limiting the records it looks up. The documentation
warns that a page with no rule is open to anyone who can reach it.

**Why:** the constitution (Article XII) says who may change a record's preferences is never this
package's decision, and the README prefers what an experienced Django developer would recognise.
A built-in default, such as signed-in only, would be a decision the package is forbidden to make
and one a developer would not expect from a Django editing view. The risk is a page left open by
mistake. FR-019 answers it in the documentation, and the package installs no URL by itself
(FR-001), so nothing is reachable until a developer routes it.

**ADR:** docs/adr/0003-the-preferences-page-is-a-detail-view-with-no-access-rule.md

## D4. Back to the same page after saving, with a message when messages are on

**Ambiguous:** where the person goes after a successful save, and whether they are told.

**Chosen:** back to the same page by default, which the host project can change. A success
message is added when Django's messages framework is enabled, and the page works without it.

**Why:** a preferences page is usually revisited rather than left. Django's messages framework is
part of Django, so using it when present adds no dependency, and requiring it would break projects
that do not enable it.

**ADR:** none — a default a project overrides with `success_url`; nothing downstream inherits it

## D5. Same-named preferences in two groups stay apart

**Ambiguous:** two apps' groups may each declare, say, `theme`.

**Chosen:** each preference belongs to its group on the page, and values never cross.

**Why:** G1 lets any installed app add its own group, and apps do not coordinate their field
names. A clash would make one app's preference silently overwrite another's.

**ADR:** none — follows from the form prefix, local to the page

## D6. Saving writes the preferences and nothing else on the record

**Chosen:** saving the page writes only the record's preferences.

**Why:** the record is often the user model or another model with its own fields, edited
elsewhere at the same time. A save that rewrote every field could undo someone else's change to
an unrelated field.

**ADR:** none — FS-001's `save()` already writes only the preferences (ADR 0001)

## D7. The groups shown are whatever FS-001 says is declared for the model

**Chosen:** the page asks FS-001 for the groups and shows all of them. It neither filters them nor
looks further itself.

**Why:** keeps the page from depending on how groups are found, so inheritance (R3) reaches the
page with no change. Choosing a subset of groups for one page was not asked for (Assumptions).

**ADR:** none — the page reads whatever the registry reports; the registry's rules are ADR 0002

## D8. A model with no preferences fails clearly

**Chosen:** using the page for a model that has not been given preferences fails with an error
that names the problem.

**Why:** that is a developer's mistake, and a clear error at first use is cheaper to act on than a
page that opens empty.

**ADR:** none — the registry's own error, raised on first use

## D9. No sketch

**Chosen:** `sketch=none`.

**Why:** the page is a plain form with no visual design of its own. The package deliberately
ships unstyled markup (README, "A user interface framework" under what it is not), and how it
looks is left to the host project and, later, to user interface packages (R4). Everything the
spec asks of the page is behaviour a test can assert: what is shown, what is saved, the errors,
the access rules, the labels on controls. There is nothing here that only a person looking at it
can decide. A user-facing form would usually be prototyped first, and this is one, but its layout
is not this package's to judge. That judgement belongs to R4.

**ADR:** none — a process choice for this feature, not a decision about the code

## D10. A new domain term: preferences page

`CONTEXT.md` has no name for the page. The spec calls it the **preferences page**. The build adds
it to `CONTEXT.md` in the same pull request.

**ADR:** none — a glossary entry, recorded in CONTEXT.md

## D11. Two stories for developers, one for users

The issue names two people. A user changes a record's preferences (Story 1). A developer routes
the page and sets who may use it (Story 2). Pointing the page at the signed-in person is its own
story (Story 3) because the issue asks for it by name and it is a distinct thing a developer does,
though it uses Story 2's page. It is P2 because it adds no capability that Stories 1 and 2 do not
already provide.

**ADR:** none — how the specification was split into stories

## D12. A group's legend is its name, not translated text

**Chosen:** each group on the page is headed by the group's registered name with a capital first
letter.

**Why:** FS-001 gives a group a name and no human label, and adding one would be public API that
nothing in this specification asks for. The name is the host project's own text, chosen in its
own code, so FR-017 (text the page itself shows) does not reach it. A project that wants
different words overrides the template. Raised by the design review (SPEC-002, low).

**ADR:** none — a template detail a project overrides; restyling points are R4

## D13. The example project gains accounts and both kinds of page

**Chosen:** the example project gets a user model that carries preferences, sign-in, the
standard development accounts, a page for each project behind a permission, and a page for the
signed-in person's own preferences.

**Why:** no requirement asks for it, but every acceptance scenario in Story 2 and Story 3 is about
who is signed in, and the merge review of a page is done by opening it. The example is also where
SC-006 ("the documentation's example works as written") can be seen running in a real project,
not only in the test suite. It ships nothing in the package. Raised by the design review
(SPEC-003, low).

**ADR:** none — the example project is not part of the package

## D14. The page protects itself against forged submissions

**Chosen:** `PreferencesView.dispatch()` is wrapped in `csrf_protect`.

**Why:** the page writes to a record, and the CSRF middleware is a setting a project can remove.
Django's own sign-in and password views protect themselves the same way
(`django/contrib/auth/views.py`), while its generic editing views rely on the middleware. One
decorator removes the dependency on a setting the package cannot see, and it does nothing extra
when the middleware is present. Raised by the design review (SEC-001, low).

**ADR:** none — one decorator on the view, noted in ADR 0003
