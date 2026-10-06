# Deployment And Acceptance

Use the checks relevant to the service and requested change. Unknown platform support or an incompatible runtime is a prerequisite to resolve, not a reason to force installation or expand the deployment.

## Installation And Accounts

Resolve the intended upstream release, package repository, artifact, or image and its supported OS/architecture. Select a reproducible version when the deployment method supports it. Inspect integrity/signature evidence supplied by the release source; record the chosen source and version without copying credentials.

Check what an installer changes: repositories, system packages, accounts/groups, services, network rules, and data. Existing installation owners and package-manager locks must be respected. Do not install a broad tool bundle for optional features.

Run the service under an appropriate account. Inspect group memberships and reachable sockets as well as UID: membership in the group for a rootful Docker daemon grants root-level capabilities. Choose the permissions needed by the selected runtime; do not grant unrestricted sudo or Docker access merely to remove a prompt.

Provide secrets through the existing supported protected mechanism. Verify ownership and access metadata without displaying values. Application logs, rendered Compose configuration, environment dumps, and command arguments can expose secrets; use selective checks.

## systemd Services

- Resolve the actual unit and whether it is a system or user service. Inspect applicable overrides and startup requirements; do not assume the same manager or privileges across both.
- Validate unit/configuration changes with the supported tools. Reload the manager when required, and restart or reload only affected services under authorization.
- Check effective runtime account, working directory, required paths, state, recent bounded logs, and listeners. Detect restart loops rather than accepting a momentary active state.
- Where needed, configure a suitable restart policy, delay, and start limits. Verify failure visibility; restart limits can leave a unit failed, so automatic restart is not an alerting substitute.
- When continuous operation is requested, check enablement and applicable user-session/linger behavior. Enabling a service is configuration evidence, not proof of an actual reboot test.

## Docker Compose Services

- Reuse the intended Compose files, project name, profiles, and environment. Check the selected service configuration without printing resolved secrets. Record the image version or digest appropriate to the deployment.
- Identify bind mounts, named/external volumes, networks, and required ownership before startup. Check persistence at the actual application data location.
- Establish dependency readiness and migration ordering from the application contract. Use a readiness condition or probe instead of an arbitrary sleep. Compatibility determines whether old/new applications can run during migration.
- Change only the intended services and required dependencies. Verify all intended instances, available health checks, bounded logs, and restart counts.
- Inspect published host addresses and ports, including IPv6 where applicable. Rootful Docker bridge publication may bypass UFW filtering; a UFW allowlist alone does not establish container exposure.
- Do not use `docker compose down -v`, prune volumes, or grant privileged mode/host mounts to resolve a deployment failure without the corresponding explicit scope.

## Functional And Operational Acceptance

Exercise the intended client route: a message handled by a bot, an authenticated API operation, a tunnel used by its client, or the equivalent for the selected service. Distinguish local health, external connectivity, authentication, and actual function. Also check that a private endpoint remains unavailable from a relevant unauthorized route when that boundary is in scope.

Determine whether resource limits, log retention, restart-failure alerts, and service/data monitoring are needed for continuous operation. Check existing mechanisms first; do not deploy a monitoring stack or create message-channel integrations without authorization.

Report each applicable check as passed, failed, partially verified, or not exercised. A dry run or disabled external test cannot support a live-service acceptance claim.

## Sources

- [systemd service behavior](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html): startup and restart semantics.
- [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/): dependency conditions and readiness.
- [Docker daemon access](https://docs.docker.com/engine/install/linux-postinstall/): Docker group privileges.
- [Docker firewall behavior](https://docs.docker.com/engine/network/packet-filtering-firewalls/): published ports and host firewalls.
