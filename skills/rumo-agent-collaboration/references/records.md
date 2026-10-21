# Run Records And Resuming

Read when continuing delegated or transferred work in a new conversation, or when a record looks wrong.

## Where Records Live

`agent_run.py` writes each run to `<runs-dir>/<run-id>/`. The directory is `--runs-dir` when given, else the `RUMO_AGENT_RUNS_DIR` environment variable, else `~/.rumo-agent-runs/`. Records stay outside product repositories by default; never commit them.

```text
<run-id>/
  .lock              OS-owned metadata lock; leave it in place after a crash
  meta.json          CLI, a copy of the adapter used, executable, version, cwd, access, model, session_id, turns, outcomes
  turns/<n>/
    prompt.md        the brief, sent on stdin or as the prompt file
    events.jsonl     the CLI's JSON event stream (stdout.txt for a text-output adapter)
    stderr.log
    final.md         the last reply, when one was found
```

`resume` uses and revalidates the adapter copy in `meta.json`; start a new run to pick up changed flags. A disable decision in either that snapshot or the current selected adapter blocks recovery without rewriting the snapshot. `status` includes `disabled_reason` and withholds the interactive resume command for disabled runs. Notes and safe cancellation remain available. Do not paste tokens or keys into a brief; name where they live instead. Raw CLI output may contain sensitive material, so keep records private and inspect them before sharing.

## Turn States

| State | Meaning |
|---|---|
| `created` | written, not yet launched |
| `launched` | process started; the session is not yet confirmed |
| `session-known` | the CLI reported or accepted the session ID |
| `exited` | exit code 0 and a final reply found |
| `failed` | non-zero exit, an error event, or no final reply |
| `timed-out` | stopped at `--timeout`; the session may hold partial work |
| `cancelling` | cancellation reserved; completion cannot overwrite it |
| `interrupted` | recorder caught an interruption and stopped its child |
| `launch-failed` | no child was launched; inspect the recorded error |
| `cancelled` | stopped by `cancel` while its process was provably ours |
| `abandoned` | the recorded process is confirmed gone or its PID has a different strong identity; marked by `cancel` after session inspection |

Native subagent and Orca runs are tracked by their own runtimes. When you use them, put their IDs in your report or a handoff document instead of in this record, so there is one source of truth for each run.

Record updates and launch/PID publication share a per-run lock. Cancel cannot slip between a visible `created` record and PID publication. Terminal states stay terminal, while late output can add diagnostics. A failed stop retains a running state and `cancel_error`, rather than claiming cancellation succeeded. Windows ownership uses a typed process handle and creation time. Linux/WSL uses `linux:<boot-id>:<start-ticks>` from the kernel boot ID and `/proc/<pid>/stat`; a system reboot changes the identity. Only Windows and Linux/WSL currently support starting or resuming a turn; other platforms refuse before launch.

`status` exposes `process_status` as `owned`, `gone`, `foreign`, or `unknown` for an active turn. `process_alive` is null for unknown identity, true for owned, and false when gone or foreign. Unknown identity is not proof that a process has exited. An unreadable identity, legacy timestamp, or unknown cancellation owner blocks automatic stopping and abandonment. These checks reduce PID reuse mistakes; they do not make checking identity and sending a signal atomic or prove that a CLI has no detached descendants.

When a cancellation recorder dies, inspect the session, then run `cancel` again to reconcile the stale `cancelling` turn. A live or unknown cancellation owner blocks a duplicate cancel. Records are not automatically migrated. A running legacy POSIX record with only a `ps` timestamp cannot prove ownership: inspect it manually, and do not cancel or resume automatically. After manually confirming the old work has stopped, use a fresh run rather than editing its identity to pass a check. New readers accept records without `access_env` or a cancellation owner. Older runners do not enforce `disabled_reason` or understand the new identity and state semantics: use this runner, not an older copy, for these records.

## Resume In A New Conversation

1. Run `status <run-id>` and read `meta.json`, the last `final.md`, and any `outcomes`.
2. Check the real state: the working directory's branch, HEAD, and uncommitted files, and whether the backend session still exists.
3. When the record and reality disagree, such as files changed after the last recorded turn or a turn with no recorded end, report the gap before acting. Run `cancel` to mark a dead turn `abandoned` only after checking the session.
4. Confirm who owns the task now. When the last outcome is `transferred`, the receiver owns it; do not resume it as a writer unless the user hands it back.
5. Continue with `resume` or the recorded interactive command. A session the CLI no longer has cannot be resumed: start a new run with a fresh brief built from the record.
