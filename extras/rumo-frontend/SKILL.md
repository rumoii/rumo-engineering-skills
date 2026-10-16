---
name: rumo-frontend
description: Use when building or refactoring frontend pages in an existing application, starting or troubleshooting a local frontend development server (package scripts, backend proxy, ports, certificates, micro-frontends), or when explicitly asked to capture browser evidence such as before-and-after screenshots, state sequences, DOM evidence, or a short GIF. Do not capture persistent visual evidence merely because frontend code changed.
---

# Rumo Frontend

Choose the mode that matches the request and read its reference before acting.

| Mode | Use for | Reference |
| --- | --- | --- |
| UI | Page work, component reuse, layout and visual consistency | [references/ui.md](references/ui.md), plus [page-patterns.md](references/page-patterns.md) and [visual-consistency.md](references/visual-consistency.md) when aligning layouts |
| Dev server | Starting, configuring, or repairing a local development server | [references/dev-server.md](references/dev-server.md) |
| Browser evidence | Persistent screenshots, state sequences, DOM evidence, or GIFs the user asked for | [references/browser-evidence.md](references/browser-evidence.md) |

## Shared Boundaries

- Confirm the real repository, package manager, route, and intended backend before editing or starting anything. Use `rumo-project-profile` when project-specific commands, proxy rules, or design references exist.
- Never point a development server or browser at an environment whose purpose is unclear. Operate only on localhost or an environment the user identified as development or test; production stays read-only unless the user authorizes the exact action.
- Preserve routes, APIs, permissions, keyboard behavior, and loading, empty, error, disabled, and validation states.
- Use an isolated automation browser profile by default. Let the user type passwords and one-time codes; never extract credentials from a browser profile.
- Keep evidence capture local. Committing, uploading, or publishing evidence is a separate action that needs explicit approval.
- A successful build does not prove proxy, authentication, or browser behavior; report which of those were actually exercised.

Run `scripts/probe_frontend_ui.py --repo <path>` for a read-only inventory of manifests, source roots, and likely component libraries.
