# Page Patterns

Use the target application's existing patterns as the authority. Compare at least one adjacent page with the same interaction shape before introducing a new layout.

Every pattern preserves loading, empty, error, permission, disabled, validation, and responsive states. The notes below add what each pattern must handle and where it usually breaks.

## List With Filters

- Filters above results; applying, clearing, and paging keep each other consistent, and the state survives refresh or back navigation when the product does so elsewhere.
- Distinguish "no data yet" from "no results for these filters", and offer to clear filters in the second case.
- Loading must not blank a list the user is reading; show progress over or beside the existing rows.
- Batch actions appear with selection and say how many items they affect.

## Create And Edit Form

- Validate at the field and again on submit; server errors land on the right field or in a summary.
- Disable or guard the submit button while saving to prevent duplicate requests.
- Warn before discarding unsaved changes; reset stale errors and values when the form reopens.
- Edit mode loads current values before enabling input.

## Detail View, Drawer, Or Dialog

- Handle a missing or deleted record and a record the user may no longer access.
- Long content scrolls inside the body while the header and actions stay reachable.
- Closing returns the user to the same place in the list.

## Tabs

- The selected tab is reflected in the URL when users need to share or return to it.
- Switching tabs does not discard unsaved input in another tab without warning.
- Inactive tabs load lazily when their data is expensive.

## Dashboard

- Each figure states its time range, unit, and freshness.
- One slow or failed widget shows its own error without breaking the rest.
- Keep a metric's color and position stable across the page.

## Multi-Step Wizard

- Show the current step and total; allow going back without losing entered data.
- Validate each step before moving on; the final step summarizes what will happen.
- Define what happens on refresh or abandonment halfway through.

## Import And Export

- Before import: accepted formats, size limits, and a template. After import: counts of accepted, rejected, and skipped rows, with reasons for rejection.
- Long exports run with visible progress or a notification instead of a frozen page.
- Exports respect the current filters and the user's permissions.

## Settings Page

- Make clear whether changes save instantly or on an explicit save, and never mix both on one screen.
- Group settings by what users try to accomplish, not by internal module.
- Dangerous settings are separated, explained, and confirmed.
