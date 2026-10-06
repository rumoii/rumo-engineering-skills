# Access Changes And Recovery

## Before Changing The Management Path

Identify the exact host, current and proposed access path, authorized changes, active configuration owner, and required privileges. Identify whether a provider firewall, host firewall, container rules, proxy, or VPN also controls the route.

Keep the current management session open. Establish an independent recovery path, such as a tested provider console or alternate management route, including the account and elevation ability needed for recovery. A console button or undocumented password is not a tested recovery path. If this protection is unavailable, stop the access change and report the prerequisite.

Before applying the change, retain the relevant current configuration in an authorized restricted location and define concrete recovery steps appropriate to that baseline. Verify the backup is readable and complete enough for the intended rollback. Distinguish a reviewed recovery procedure from an actually exercised restore; do not perform a disruptive recovery test without authorization.

Backups of SSH configuration can include host private keys. Keep them under restricted server-side access or an explicitly authorized encrypted destination; never export them to an ordinary task archive.

## Validate And Change In Stages

1. Check syntax and effective configuration using the actual platform's tools. For OpenSSH, `sshd -t` checks syntax and `sshd -T` shows effective settings; use the relevant connection context when `Match` rules apply. A single drop-in file does not establish the final policy.
2. Inspect the target version, active service/socket, effective units/overrides, generated settings, and firewall implementation. Ubuntu SSH socket behavior varies by release; configuration may feed a generator. Do not assume `Port` is ignored, reload cannot rebind, or restart necessarily kills existing sessions. Establish the actual activation mode and effective unit behavior, including `KillMode` where relevant, using target evidence and version-appropriate official sources.
3. Establish the new listener and necessary rules while preserving the old route until independent validation succeeds. Do not reset a listener list to only the new port before that validation. Avoid clearing firewall rules or temporarily opening all inbound traffic to simplify the procedure.
4. From an independent client connection, verify host-key identity, the intended account, permitted authentication, and the needed elevation. Check effective rules and actual listeners as well.
5. Close the old route only after the new route is verified and closure is in scope. Verify the intended resulting access and exposure.

For privilege changes, keep an existing authorized administration path until the new account and privileges are verified. Do not assume a normal user is unprivileged when it has broad sudo rights or access to a rootful Docker socket.

## Failure And Recovery

Stop further changes when validation fails or access is uncertain. Use the retained session or independent recovery path to inspect state. Restore only the agreed baseline and affected scope under the existing recovery authorization; otherwise present the exact recovery action for approval.

Restoring older firewall or authentication files can reintroduce exposure or remove access needed by later services. Recheck the baseline's applicability before using it. After recovery, verify independent login and relevant service behavior, and record the resulting state.

Reboot only when necessary and authorized. Plan how to regain the management connection and credentials after reboot; a prior temporary root session will not survive it.

## Sources

- [Ubuntu OpenSSH configuration](https://ubuntu.com/server/docs/how-to/security/openssh-server/): configuration precedence and syntax validation.
- [Ubuntu SSH socket activation](https://discourse.ubuntu.com/t/sshd-now-uses-socket-based-activation-ubuntu-22-10-and-later/30189): version-dependent listener control.
- [OpenSSH daemon manual](https://man.openbsd.org/sshd.8): SIGHUP re-execution; reconcile with the target release and activation mode.
- [systemd process termination](https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html): effective KillMode and termination behavior.
