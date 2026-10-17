---
name: rumo-frontend
description: Use when building, refactoring, or designing frontend pages and components, including a new interface with no existing pattern to follow or a request to improve visual quality or accessibility; starting or troubleshooting a local frontend development server (package scripts, backend proxy, ports, certificates, micro-frontends); or capturing browser evidence such as screenshots or a short GIF when explicitly asked. Do not capture persistent visual evidence merely because frontend code changed.
---

# Rumo Frontend

Choose the mode that matches the request and read its reference before acting.

| Mode | Use for | Reference |
| --- | --- | --- |
| UI | Changing pages in an existing application: component reuse, layout, visual consistency | [references/ui.md](references/ui.md), plus [page-patterns.md](references/page-patterns.md) and [visual-consistency.md](references/visual-consistency.md) when aligning layouts |
| New design | A page, component, or application with no existing pattern to follow, or an explicit request to make the interface look better | [references/design-quality.md](references/design-quality.md) and [page-patterns.md](references/page-patterns.md) |
| Dev server | Starting, configuring, or repairing a local development server | [references/dev-server.md](references/dev-server.md) |
| Browser evidence | Persistent screenshots, state sequences, DOM evidence, or GIFs the user asked for | [references/browser-evidence.md](references/browser-evidence.md) |

An established design system or adjacent page always outranks the defaults in `design-quality.md`. Before handing back any UI or new-design change, check it against [references/accessibility.md](references/accessibility.md).

## Shared Boundaries

- Confirm the real repository, package manager, route, and intended backend before editing or starting anything. Use `rumo-project-profile` when project-specific commands, proxy rules, or design references exist.
- Never point a development server or browser at an environment whose purpose is unclear. By default operate only on localhost or an environment the user identified as development or test. Production access needs the user's explicit go-ahead and stays read-only unless the user authorizes the exact change.
- Preserve routes, APIs, permissions, keyboard behavior, and loading, empty, error, disabled, and validation states.
- Use an isolated automation browser profile by default. Let the user type passwords and one-time codes; never extract credentials from a browser profile.
- Temporary renders and screenshots for self-checking are expected. Keep evidence capture local; persisting, committing, uploading, or publishing it is a separate action that needs explicit approval.
- A successful build does not prove proxy, authentication, or browser behavior; report which of those were actually exercised.

Run `scripts/probe_frontend_ui.py --repo <path>` for a read-only inventory of manifests, source roots, and likely component libraries.
