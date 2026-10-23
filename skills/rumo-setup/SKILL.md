---
name: rumo-setup
description: Use when the user runs rumo-setup, asks to configure or change which agent CLIs, models, and reasoning efforts the Rumo skills use for multi-model review, multi-design comparison, or default delegation ("配置 agent", "把评审换成 grok", "思考强度改成 high"), or when a Rumo script reports that agents are not configured. Probes every chosen lane with one tiny read-only turn before saving. Do not use to delegate a task now (use rumo-agent-collaboration) or to configure project profiles (use rumo-project-profile).
---

# Rumo Setup

Record once per machine which other agents the Rumo skills may call, with which model and effort, so later reviews and delegations neither guess nor ask again. Only scripts read the file, so it adds nothing to a session's context until a skill asks for a role.

## What Gets Configured

| Setting | Used by | Meaning |
| --- | --- | --- |
| `review` lanes | `rumo-review` panel | Extra reviewers of the same diff |
| `design` lanes | `rumo-plan` design panel | Extra designers drafting independent options |
| `delegate` lane | `rumo-agent-collaboration` | The one agent used when the user hands work off without naming a CLI |
| `auto_panel` | review and design panels | What the agent may do when it judges, on its own, that a panel is worth it: `ask` (default), `allow` (state the lanes, then launch), or `off` (panels only when the user asks) |

A lane is `cli[:model][@effort]`, such as `codex:gpt-6.1-sol@high` or `claude@max`; leaving out the model or effort uses the CLI's own default. One CLI may fill several lanes with different models, such as two providers configured inside pi. The current agent always counts as one lane of a panel and keeps the model chosen in its own client, so one extra lane already gives two independent views. Every extra lane spends that provider's quota each time a panel runs.

## Workflow

1. Resolve `../rumo-agent-collaboration/scripts/agent_config.py` and `../rumo-agent-collaboration/scripts/agent_run.py` from this skill's directory. If they are missing, stop and say that `rumo-agent-collaboration` must be installed beside this skill.
2. Read the current state: `agent_config.py show` (exit 3 means a first run) and `agent_run.py list`. For each installed, usable adapter, run `agent_config.py models <cli>` to get the models it offers, with per-model efforts and default effort when the CLI reports them. Mark adapters whose `verified.live_run` is false as untested.
3. Ask everything in one round, each question with a recommendation:
   - First run: recommend, for `review` and `design`, one lane from a provider other than the current client's, at `high`; for `delegate`, that provider at `medium`; and `auto_panel: ask`. Offer the listed models as choices, each with the efforts it accepts, plus "CLI default"; never invent an ID the listing does not show. When a CLI cannot list its models, ask for the ID or keep the default.
   - Rerun: show the current values and change only the items the user names. Never offer a reset to the defaults.
   - State that the probe in step 4 sends one fixed sentence and no repository content, and spends a little quota per lane.
4. Probe the new or changed lanes before writing: `agent_config.py check --probe --lane <lane> ...`, adding `--executable <cli>=<path>` for a CLI that is not on PATH. When a lane fails, report its error, such as not signed in, unknown model, or an effort the CLI rejects, and write nothing for the roles that use it.
5. Write each changed role with `agent_config.py set-role <role> --lane <lane> ...`, and `auto_panel` with `agent_config.py set-auto-panel <value>`. Each command replaces only its own setting.
6. Run `agent_config.py show` and report.

## Stop Conditions

- Do not sign in to a CLI, change its configuration, or switch to another model or provider to make a probe pass; report the failure and let the user decide.
- Never put an API key, token, or password in the configuration; each CLI keeps its own sign-in.
- When the script refuses a value, do not edit the JSON by hand to get around it.
- Do not write defaults the user has not seen; a first run writes only after the user accepts or changes the recommendations.

## Report

The configuration path, every role with its lanes, `auto_panel`, each probe's result and run ID, any lane that is untested or failed, and how to change it later: run this skill again, or ask for a specific change such as "make review use grok at high".
