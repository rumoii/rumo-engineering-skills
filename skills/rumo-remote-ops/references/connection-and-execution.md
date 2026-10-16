# Connection And Execution

## Access And Identity

Use the connection method declared in local instructions, including any proxy or bastion. An IP address alone is not host-key verification. For an unknown or changed key, obtain the expected fingerprint through a trusted independent channel before updating trust; do not delete known-host entries or use `StrictHostKeyChecking=no` to silence the event.

On Windows, verify which SSH executable, authentication agent, and proxy are actually used. WSL and a remote agent do not automatically inherit Windows credentials or loopback services. Resolve the intended environment without copying private keys or installing another SSH stack by default.

Examples of small discovery queries, executed in the remote Linux shell:

```bash
hostname
id
cat /etc/os-release
```

Choose additional queries from the task: disk usage for a disk question, selected unit state for a service question. Do not run a mandatory whole-host probe. Access metadata and public fingerprints may be recorded; secret values must not appear in arguments, terminal capture, or reports.

## Shell And Terminal Boundaries

- State whether a command runs in local PowerShell, local Bash, or remote Bash. Check which shell expands variables, substitutions, quoting, and redirections before submission.
- Prefer a small remote command or a reviewed script over deeply nested shell strings. A submitted script is still a change-capable payload: check its content and authorization before sending it.
- Read each consequential result before issuing dependent steps. Input accepted by a terminal is not a completed command. Avoid stacking commands behind an interactive prompt or pager.
- For systemd queries use `--no-pager`. In an interactive Linux session, task-local `SYSTEMD_PAGER=cat`, `PAGER=cat`, and `SYSTEMD_COLORS=0` can make output readable; do not persist them in shell configuration merely for collection.
- Bound logs by unit, time range, and line count. Avoid full environment/configuration dumps and command lines containing credentials. Filter sensitive content before it crosses into chat or evidence; later redaction cannot undo disclosure.
- Use finite waits and output reads so progress remains observable. A missing command or denied query is an evidence gap, not permission to install tools or escalate access automatically.

## Interrupted Or Uncertain Execution

Record the last confirmed step and the uncertain operation. Reconnect through the verified route, confirm identity, and inspect the relevant process, package state, unit, configuration, or data result. The remote process may still be running after the client disconnects.

If still running, observe it rather than launch another copy. If completed, verify its result and proceed to the next step. If partially applied, determine what remains and whether the authorized recovery can safely run. If state cannot be established, report uncertainty and stop dependent mutations.

Idempotence must come from the operation's actual behavior. Do not replay migrations, restore jobs, file transfers with destructive options, or restarts just because the wrapper command failed.

## Sources

- [OpenSSH client configuration](https://man.openbsd.org/ssh_config): host-key checks, agent forwarding, batch mode, timeouts, and proxy behavior.
- [Microsoft OpenSSH key management](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement): Windows authentication-agent ownership and key use.
