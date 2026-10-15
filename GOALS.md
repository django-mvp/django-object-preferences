# Goals

These are the standing directions `django-object-preferences` works toward. Each one is a capability or
quality to steer by, not a task that gets ticked off. Whether any goal has been served well enough
is decided in the roadmap, the feature specs, and review, never by the goal itself.

This file carries no version numbers or release plan; that lives in the roadmap. For what the
package is, what it stays out of, and the principles that settle a close call, read the
*Scope & philosophy* section of the [README](README.md).

Importance is a tag on each goal, not a ranking:

- **Essential** — not worth adopting without it.
- **Expected** — a complete, dependable version is expected to have it.
- **Aspirational** — a genuine want whose absence never makes the package incomplete.

| ID | Goal | Importance | Status | Notes |
|----|------|------------|--------|-------|
| G1 | Once a model carries preferences, any installed app can add its own to it without a new model, table or migration | Essential | | |
| G2 | Reading a record's preferences costs nothing beyond loading the record | Essential | | |
| G3 | A preference nobody has changed always reads its current default, and stored values that no longer fit never break a page | Essential | | |
| G4 | People can change a record's preferences on a page, while the host project decides who has permission | Essential | | |
| G5 | Preferences declared for a model reach the models that inherit from it | Expected | | |
| G6 | Works in any Django project without a user interface package, and its page is simple for one to restyle | Expected | | |

_Written 2026-10-15. Revise as the goals change._
