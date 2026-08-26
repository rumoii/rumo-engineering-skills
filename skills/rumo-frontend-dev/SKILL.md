---
name: rumo-frontend-dev
description: Use when starting, configuring, or troubleshooting a local frontend development server, including repository discovery, package-manager commands, backend proxies, occupied ports, host binding, certificates, and micro-frontend runtime configuration.
---

# Frontend Development Server

Confirm the real repository, package manager, scripts, runtime configuration, and intended backend before starting anything. Use [`rumo-project-profile`](../rumo-project-profile/SKILL.md) when project-specific commands or proxy rules exist.

## Workflow

1. Read package manifests, workspace configuration, environment files, and repository instructions.
2. Identify the intended application or workspace and the exact development script.
3. Resolve the backend proxy from explicit user input, the selected profile, or existing local configuration. Never silently point a development server at an environment whose purpose is unclear.
4. Check requested ports and choose an alternative only when the application supports overriding them.
5. Start the server with the repository's package manager and preserve its output for troubleshooting.
6. Verify the bound address, HTTP response, runtime configuration, console errors, and failed network requests.

For micro-frontends, verify both the host application and child entry URL, public path, cross-origin behavior, and runtime API base. A successful build does not prove that the local proxy or authenticated browser workflow works.

Do not change committed proxy configuration merely to start a one-off local session unless the user requested that change.
