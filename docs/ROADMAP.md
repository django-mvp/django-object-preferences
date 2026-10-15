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

*delivered in [#7](https://github.com/django-mvp/django-object-preferences/issues/7) · advances G1, G2, G3*

A host project turns preferences on for a model it owns by adding one field, at the cost of one migration. Any installed app declares a named group of preferences for that model with an ordinary Django form in its `preferences.py`, and the package finds it at start-up. Every record reads its preferences without a database query, typed as the form's fields produce them. A preference nobody changed reads its current default, and stored values that no longer fit read the default instead of raising. Code changes and saves preferences with the form's own validation. The README and a small example project show all of it, and the editing page and everything after it build on this.

Serves G1, G2 and G3.

### R2 — A page to change a record's preferences

*delivered in [#8](https://github.com/django-mvp/django-object-preferences/issues/8) · advances G4, G6*

Each record has a page, `PreferencesView`, that shows every preference group declared for its model and saves them together with each group's own validation, so one invalid value saves nothing. A host project routes the page wherever it likes and restricts it with Django's ordinary access tools, because the page adds no rule of its own, and the README warns that a page routed with no rule is open to anyone. The README shows the common case of a page where each signed-in person changes their own preferences. The markup is a plain, accessible HTML page that needs no user interface package, and the example project shows both kinds of page behind a sign-in.

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
