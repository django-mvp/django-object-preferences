# Roadmap — django-object-preferences

**Date:** 2026-10-15

This document was designed against [GOALS.md](../GOALS.md). See also [CONTEXT.md](../CONTEXT.md) for domain terminology and [CONSTITUTION.md](../CONSTITUTION.md) for project standards.

## Versioning

| Version | Gate |
|---|---|
| `0.0.x` | Building toward the Essential goals. Pre-viable, expect churn, nothing published |
| `0.1.0` | All Essential goals delivered. The minimum usable release, and the first publish |
| `0.1.x` → `0.x` | Advancing the Expected goals, at whatever granularity the work takes. Patches are fixes |
| `1.0.0` | All Expected goals delivered. The complete, dependable release |
| `1.x` | Stable line: non-breaking fixes and additive features only |
| `2.0` | The next major, where breaking changes go |

A goal is not one minor release: some take several, and one release can move two. Once `1.0` ships, a breaking change never goes out as `1.x`. It waits for the next major.

*Aspirational goals may be developed against v2 or v1 as required.*

## Essential goals: v0.1.0

Everything needed to reach a minimum usable release.

### R1 — Preferences declared for a model and read from its records

*feature · advances G1, G2, G3*

The foundation everything else builds on. A host project turns preferences on for a model it owns, and any installed app can then declare a group of preferences for that model and read them back from any of its records. It comes first because the editing page and everything after it read and write what this item defines.

**Deliverables:**

- A host project can turn preferences on for any model it owns, at the cost of a single migration on that model.
- Any installed app can declare a named group of preferences for a model, each preference with a type, validation and a default, and the package finds those declarations without the host project listing them.
- Reading a preference from a record already loaded makes no further database query.
- A preference nobody has changed reads its current default, so changing a default reaches every record still on it.
- A stored value that no longer matches its declaration, or belongs to a preference that no longer exists, never raises. The current default is used instead.
- Preferences can be changed and saved from code, with the same validation a person would meet on a page.
- A small example project and README documentation showing a preference declared, read and changed.

Serves G1, G2 and G3. Out of scope: any page or view, and model inheritance beyond the model a group was declared for.

### R2 — A page to change a record's preferences

*feature · advances G4, G6*

Once preferences can be declared and read, people need somewhere to change them. This item gives every record a page listing the preference groups declared for its model, with the host project deciding where that page lives and who may use it. It also gives a signed-in person a page for their own preferences, which is the case nearly every host project has first.

**Deliverables:**

- An editing page for one record that shows every preference group declared for its model and saves changes with full validation.
- The host project decides who may open the page for a given record, using Django's ordinary permission tools.
- A ready-to-mount page where a signed-in person changes their own preferences.
- Plain, accessible markup that works in any Django project without a user interface package.

Serves G4 and G6. Out of scope: styling for any particular user interface package, and admin integration.

## Expected goals: v1.0.0

What a complete, dependable release adds.

### R3 — Preferences that follow model inheritance

*feature · advances G5*

A group declared for a parent model should reach every model that inherits from it, so a host project with a polymorphic hierarchy declares shared preferences once. This matters as soon as preferences sit on a base model with several concrete children.

Serves G5. Out of scope: preferences shared between unrelated models.

### R4 — A page that a user interface package can restyle

*feature · advances G6*

The editing page from R2 is plain markup. A user interface package that wraps this one needs to replace its layout and the rendering of each group without copying the view. This item makes those points explicit and documented.

Serves G6. Out of scope: shipping any styled templates of its own.

### R5 — Preferences in the Django admin

*feature · advances G4*

Staff often need to see or correct a record's preferences without signing in as its owner. This item puts a record's preference groups in its Django admin page, with the same validation as the editing page.

Serves G4. Out of scope: bulk editing across many records.
