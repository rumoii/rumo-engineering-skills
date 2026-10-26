---
name: rumo-setup
description: Use when the user runs rumo-setup, asks to configure or change which agent CLIs, models, and reasoning efforts the Rumo skills use for multi-model review or default delegation ("配置 agent", "把评审换成 grok", "思考强度改成 high"), or when a Rumo script reports that agents are not configured. Probes every chosen lane with one tiny read-only turn before saving. Do not use to delegate a task now (use rumo-agent-collaboration) or to configure project profiles (use rumo-project-profile).
---

# Rumo Setup

Record once per machine which other agents the Rumo skills may call, with which model and effort, so later reviews and delegations neither guess nor ask again. Only scripts read the file, so it adds nothing to a session's context until a skill asks for a role.

## Talk To The User

Most users meet these settings for the first time here. Speak in the user's language and in plain words, explain a setting before asking about it, and give every recommendation a one-line reason. Never show lane syntax to the user: present `codex:gpt-6.1-sol@high` as "Codex · gpt-6.1-sol · effort high"; the syntax belongs in commands only. Word every question, option label, and description from the table below, on reruns too, and never coin a name for a setting.

| Setting | Used by | Explain it as |
| --- | --- | --- |
| `review` lanes | `rumo-review` panel | The agents that independently re-check a change after the current agent reviews it |
| `delegate` lanes | `rumo-agent-collaboration` | The agent that takes work the user hands off without naming one. Different kinds of work can go to different agents, such as tests to one and implementation to another; work that fits none goes to the first |
| `auto_panel` | review panel | Whether, when the user has not asked but the current agent judges a change risky, it also brings in the configured agents to look: ask the user first (`ask`, default), say which agents and start (`allow`), or never offer and wait to be asked (`off`). Call it by this behavior, never a panel, committee, or jury |
| effort | every lane | How hard the model thinks: higher is more careful, slower, and spends more quota. Leaving out the model or effort uses the CLI's own default |
| probe | step 5 | One fixed sentence sent to each new agent before saving, to prove it answers; it spends a little quota and sends no repository content |

The current agent always takes part in a panel with the model chosen in its own client, so one extra lane already gives two independent views. One CLI may fill several lanes with different models, such as two providers configured inside pi. A lane spends its provider's quota only when it runs.

There is one configuration per machine and no per-repository file. For one task, the user names the lanes in the request. For a repository that should always use other lanes, point `RUMO_AGENTS_CONFIG` at a separate file while working there, for example with direnv, and run this skill with it set.

## Workflow

1. Resolve `../rumo-agent-collaboration/scripts/agent_config.py` and `../rumo-agent-collaboration/scripts/agent_run.py` from this skill's directory. If they are missing, stop and say that `rumo-agent-collaboration` must be installed beside this skill. Also resolve `../rumo-coding-guidelines/scripts/baseline_block.py` for step 7.
2. Read the current state: `agent_config.py show` (exit 3 means a first run) and `agent_run.py list`. For each installed, usable adapter, run `agent_config.py models <cli>` to get the models it offers, with per-model efforts and default effort when the CLI reports them. An adapter whose `verified.live_run` is false is experimental: tell the user it has not completed a real run yet and may fail.
3. On a first run, before any question, say in two or three sentences what this is for: it lets the current agent call other AI coding tools installed on this machine to re-check reviews or take over work; it is optional, and every other skill works without it; and a tool's quota is spent only when that tool is called.
4. Present one recommended configuration as a plain table with a reason per row, and ask in one round whether to accept it as a whole or change items:
   - First run: recommend, for `review`, one lane from a provider other than the current client's, at `high`, because a different model family misses different things; a second lane mostly adds cost. Pick that provider's strongest model for this role, never a lightweight or flash tier, which adds little over the current agent's own review. For `delegate`, recommend that provider at `medium`, because routine work rarely needs the deepest effort, then ask whether different kinds of work, such as tests and implementation, should go to different lanes. Also offer a lane on the current client's own CLI with a cheaper model, such as Claude Code with sonnet at medium, for routine work: the current client runs it as its own subagent, which costs less than its main model and starts no other CLI. Recommend `auto_panel: ask`, so the user decides each time extra quota is spent. Offer the listed models as choices, each with the efforts it accepts, plus "CLI default"; never invent an ID the listing does not show. When a CLI cannot list its models, ask for the ID exactly as that CLI's own model picker shows it, or keep the default; do not look IDs up in the CLI's model catalog or configuration files, which list models it knows rather than models the user can reach.
   - When no other supported CLI is installed, say that no setup is needed and every skill works with the current agent alone. Offer two choices: a lane on the current CLI with another model, which reviews with fresh context but shares its provider's blind spots and quota; or installing a supported CLI and running this skill again. Write nothing unless the user picks one.
   - Rerun: show the current values as a plain table and change only the items the user names. Never offer a reset to the defaults.
   - Say that the probe in step 5 sends one fixed sentence and no repository content, and spends a little quota per lane.
5. Probe the new or changed lanes before writing: `agent_config.py check --probe --lane <lane> ...`, where a lane is `[use=]cli[:model][@effort]` and a delegate use label looks like `测试=`, adding `--executable <cli>=<path>` for a CLI that is not on PATH. When a lane fails, explain the error in plain words with the user's next step: not signed in means running that CLI once and signing in; an unknown model means picking one from the list; a rejected effort means choosing one the model accepts. Until it passes, write nothing for the roles that use it.
6. Write each changed role with `agent_config.py set-role <role> --lane <lane> ...`, and `auto_panel` with `agent_config.py set-auto-panel <value>`. Each command replaces only its own setting.
7. Last, on a first run only, ask about the always-on baseline as a separate question: it writes a short block of the core `rumo-coding-guidelines` rules into the current client's user-level instruction file, so they apply even when no skill loads, such as on a small edit, and only the text between its markers is ever changed. The target is `CLAUDE.md` in `$CLAUDE_CONFIG_DIR` or `~/.claude` for Claude Code, `AGENTS.md` in `$CODEX_HOME` or `~/.codex` for Codex; for any other client, ask the user for that file's path and never guess it. Skip the question when `baseline_block.py --target <file> --refresh --dry-run` does not print `absent`. Recommend adding it; when the user accepts, run `baseline_block.py --target <file> --install`. On a rerun, offer it only when the user asks.
8. Run `agent_config.py show` and report.

## Stop Conditions

- Do not sign in to a CLI, change its configuration, or switch to another model or provider to make a probe pass; report the failure and let the user decide.
- Never put an API key, token, or password in the configuration; each CLI keeps its own sign-in.
- When the script refuses a value, do not edit the JSON by hand to get around it.
- Do not write defaults the user has not seen; a first run writes only after the user accepts or changes the recommendations.

## Report

A plain table of each role with its agent, model, and effort, each probe's result and run ID, and any lane that is experimental or failed; the baseline file and the script's result when it was offered. Add one sentence per configured role on when it will be used, such as "when you ask for a review, I review first, Codex then reviews on its own, and I merge the findings". Name the configuration path once, and say how to change it later: run this skill again, or ask for a specific change such as "make review use grok at high".
