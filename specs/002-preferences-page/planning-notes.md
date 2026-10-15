# Planning notes for FS-002

Notes on how to build this feature, carried into planning. Each one must be answered by name when
the feature is planned.

## N1. A class-based view that takes its record from `get_object()`

From the conclusions in `docs/brainstorm.md`: "The editing page is a class-based view that takes
its record from `get_object()`. Who may edit a record is the host project's decision." Pointing
the page at the signed-in person (Story 3) is then a matter of returning the signed-in user from
`get_object()`, and limiting the records it looks up is the ordinary queryset.

## N2. Validate every group before writing any of them

FR-005 makes saving all or nothing across the groups on the page, but FS-001's path for changing
preferences from code saves one group at a time. Calling it once per group would save the groups
before an invalid one and then stop. The page should validate every group first and write only
once all of them pass.
