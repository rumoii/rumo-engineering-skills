# Output Sample Provenance

These samples contain no credentials. Except for the two historical observations below, they are constructed test inputs, not captured model responses.

| Samples | Basis |
|---|---|
| `pi.jsonl` | Constructed; the tool event fields follow a local pi 1.3.0 run |
| `qwen.jsonl` | Historical read-only turn on Qwen 0.25.2; not rerun for this revision |
| `grok-error.jsonl` | Historical 1.0.41 sign-in failure; no successful model turn |
| `copilot.jsonl` | Constructed from the [official event types](https://github.com/github/copilot-sdk/blob/main/nodejs/src/generated/session-events.ts); CLI JSONL integration not run |
| `aider.txt` | Constructed plain response; [options](https://aider.chat/docs/config/options.html) |
| `cline.jsonl` | Constructed run result and agent event; [JSON output reference](https://docs.cline.bot/cli/cli-reference#json-output-for-agent-runs) |
| `goose.jsonl` | Constructed stream message and completion; [stream event source](https://github.com/aaif-goose/goose/blob/main/crates/goose-cli/src/session/mod.rs) |
| Other JSONL samples | Constructed from the corresponding adapter's known or documented event format |

No fixture establishes filesystem isolation, real session continuation, or successful development through an installed CLI.
