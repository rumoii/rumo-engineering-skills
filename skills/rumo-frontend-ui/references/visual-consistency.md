# Visual Consistency

Use this reference before finalizing a new page or UI refactor.

## Refactor Process

1. Capture the current behavior: route, key interactions, data loading, empty/error/loading states.
2. Identify the target visual pattern from nearby pages.
3. Replace layout and duplicated UI with existing components.
4. Keep API calls, permissions, route behavior, i18n keys, and persisted table IDs stable unless the task requires changes.
5. Verify visually and with relevant commands.

## New Page Process

1. Pick the page pattern from `page-patterns.md`.
2. Pick one or two reference pages in the same subapp.
3. Copy the component structure, not the business logic.
4. Define columns, actions, query params, and status mappings in stable locations.
5. Add page-local `$components` only for complex sections that are not generally reusable.

## Component Checklist

- Page shell uses the product's app view component when available.
- Query and table use existing business components.
- Toolbar actions use primary/default/danger types consistently.
- Row actions are in the operations column.
- Status fields use `UesStatusDot`, `cut-tag`, or a local status component.
- Long text uses a text overflow component, table tooltip, or clear ellipsis behavior.
- Uploads use existing upload components.
- Dialogs and drawers use CutUI primitives and project conventions.

## Layout Checklist

- Content aligns to the existing page padding, commonly 16px when using AppView.
- Query is above results.
- Batch actions are close to table selection state.
- Dialog footer order is cancel on the left, primary action on the right.
- Drawer width matches task complexity: common detail around 800px; preview/report can be wider.
- Only one main vertical scroll container exists per page area.
- Long drawer/dialog content scrolls inside body, not behind footer actions.

## Color and Theme Checklist

- Main actions use component `type="primary"` rather than custom colors.
- Danger actions use `type="danger"` and confirmation.
- Text colors use theme variables or component defaults.
- Backgrounds and borders use theme variables or component wrappers.
- No page-only primary color, page-only button system, or page-only table theme.
- Chart colors may be business-specific, but the same metric keeps the same color in one page.

## Interaction Checklist

- Success feedback uses existing message/toast conventions and refreshes the affected table/node.
- Destructive actions confirm before execution.
- Loading, empty, error, disabled, and permission-limited states are represented.
- Forms reset stale errors and loading state when closed.
- Route return/back behavior follows existing app view or breadcrumbs conventions.

## Visual QA

When a dev server/route is available, inspect the page in a browser:

- Desktop viewport: no overlap, no clipped buttons, no unwanted horizontal scroll.
- Narrow viewport: query fields wrap, toolbar remains usable, text does not cover controls.
- Tables: columns, empty state, loading state, pagination, row action menu.
- Dialog/drawer: title, body, footer, close behavior, scroll behavior.
- Theme: primary/status/text colors match existing pages.
