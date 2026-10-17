# Frontend UI

Ground the change in the real page, design system, component inventory, routes, permissions, API behavior, and responsive constraints. Use `rumo-project-profile` for private design references or product-specific component rules.

## Principles

- Reuse the application's established components and tokens when they satisfy the required behavior.
- Preserve routes, APIs, permissions, keyboard behavior, loading, empty, error, disabled, and validation states.
- Keep layout changes local to the target page unless shared ownership is proven.
- Avoid replacing working product behavior with a visually similar mock.
- Confirm the rendered DOM when component libraries, portals, scoped styles, or conditional mounting affect the visible result.

## Workflow

1. Locate the target route and component, then inspect adjacent pages and shared components.
2. Establish success criteria for structure, spacing, alignment, overflow, states, and interactions.
3. Implement the smallest coherent change using existing design tokens and component APIs.
4. Run focused lint or tests and the affected application build.
5. When browser validation is required, prefer Playwright driving an isolated browser profile; otherwise use another browser-automation tool; if none is available, report that browser validation was not done. Check visible state, console errors, failed network requests, critical interactions, and screenshots.

Run `scripts/probe_frontend_ui.py --repo <path>` for a read-only inventory of package manifests, source roots, and likely component libraries.
