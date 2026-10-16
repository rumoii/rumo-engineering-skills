# Visual Consistency

Use this reference before finalizing a new page or UI refactor.

## Refactor Process

1. Capture the current behavior: route, key interactions, data loading, empty/error/loading states.
2. Identify the target visual pattern from nearby pages.
3. Replace layout and duplicated UI with existing components.
4. Keep API calls, permissions, route behavior, i18n keys, and persisted table or column identifiers stable unless the task requires changes.
5. Verify visually and with relevant commands.

## New Page Process

1. Pick the page pattern from `page-patterns.md`.
2. Pick one or two reference pages in the same application or module.
3. Copy the component structure, not the business logic.
4. Define columns, actions, query params, and status mappings in stable locations.
5. Add page-local components only for complex sections that are not generally reusable, following the project's convention for where they live.

## Component Checklist

- The page shell uses the application's standard page or layout component when one exists.
- Query and table use existing business components.
- Toolbar actions use the component library's primary, default, and danger variants consistently.
- Row actions sit in the table's actions column.
- Status fields use the project's existing status or tag component, or a local one when none exists.
- Long text uses a text overflow component, table tooltip, or clear ellipsis behavior.
- Uploads use existing upload components.
- Dialogs and drawers use the project's dialog and drawer primitives and conventions.

## Layout Checklist

- Content padding matches adjacent pages built on the same page shell.
- Query is above results.
- Batch actions are close to table selection state.
- Dialog footer button order follows the project's existing dialogs.
- Drawer width matches task complexity and the widths already used for similar drawers.
- Only one main vertical scroll container exists per page area.
- Long drawer/dialog content scrolls inside body, not behind footer actions.

## Color and Theme Checklist

- Main actions use the component library's primary variant rather than custom colors.
- Danger actions use the danger variant and a confirmation.
- Text colors use theme variables or component defaults.
- Backgrounds and borders use theme variables or component wrappers.
- No page-only primary color, page-only button system, or page-only table theme.
- Chart colors may be business-specific, but the same metric keeps the same color in one page.

## Interaction Checklist

- Success feedback uses existing message/toast conventions and refreshes the affected table/node.
- Destructive actions confirm before execution.
- Loading, empty, error, disabled, and permission-limited states are represented.
- Forms reset stale errors and loading state when closed.
- Route return/back behavior follows the application's existing page shell or breadcrumb conventions.

## Visual QA

When a dev server/route is available, inspect the page in a browser:

- Desktop viewport: no overlap, no clipped buttons, no unwanted horizontal scroll.
- Narrow viewport: query fields wrap, toolbar remains usable, text does not cover controls.
- Tables: columns, empty state, loading state, pagination, row action menu.
- Dialog/drawer: title, body, footer, close behavior, scroll behavior.
- Theme: primary/status/text colors match existing pages.
