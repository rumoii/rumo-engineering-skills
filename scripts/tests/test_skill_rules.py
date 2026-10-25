from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

# Rules whose loss would let an agent overstep or overclaim. Merges and rewrites
# have dropped such rules before; pin each one so the loss fails CI instead of
# surfacing later. rumo-clarify and the high-assurance gate are pinned in
# test_skill_boundaries.py.
RULES = {
    "rumo-coding-guidelines": (
        "Did the user ask for it?",
        "Report unrelated problems you notice instead of fixing them.",
        "Treat review, explanation, and monitoring requests as read-only until the user asks for a change.",
        'never substitute "should work"',
        "A high-assurance final run is always a fresh run after the last edit",
        "Only after the user agrees, add it to their `AGENTS.md` or `CLAUDE.md`",
        "Do not start the review or edit any skill or instruction file unless the user accepts.",
        "A flow is a default route, not a checklist to copy",
        "read [references/task-flows.md](references/task-flows.md)",
    ),
    "rumo-database-change-safety": (
        "Start read-only.",
        "Never infer the target from a familiar hostname",
        "Approval for code changes, packaging, SSH access, deployment, or read-only inspection is not database-write approval.",
        "If the user has not already authorized that exact write, wait.",
        "Never run a destructive rollback automatically",
    ),
    "rumo-debug": (
        "Investigation is read-only by default.",
        "Database writes always go through `rumo-database-change-safety`.",
        "Never repeat the same patch without new evidence.",
        "Respect the user's explicit budget",
        "stays read-only unless the user authorizes the exact change",
        "Keep source reasoning separate from runtime proof.",
        "Use it only when service ownership is unknown",
    ),
    "rumo-filesystem-safety": (
        "Use the light path only when every one of these holds",
        "Use the full path whenever any of these applies",
        "Writing or editing a cleanup script does not authorize running it.",
        "Do not traverse a link to delete its destination.",
        "on every component of each path before deleting, not only on the target",
        "Removing a duplicate requires proof that the copies are separate objects",
        "Never create ad-hoc backup copies as part of a deletion",
        "without retrying against a broader path",
    ),
    "rumo-frontend": (
        "stays read-only unless the user authorizes the exact change",
        "never extract credentials from a browser profile",
        "persisting, committing, uploading, or publishing it is a separate action that needs explicit approval",
        "A successful build does not prove proxy, authentication, or browser behavior",
    ),
    "rumo-git-commit": (
        "Perform only the Git operations explicitly requested by the user.",
        "Preserve unrelated tracked, staged, unstaged, and untracked work.",
        "Never create a tag unless the user explicitly asks",
        "Never push unless the user explicitly asks.",
        "Write the reason as a fact about the code, its users, or the evidence, never as the conversation that led to it",
        "name the resulting state rather than the removal.",
        "Open or update a pull request only when the user asks.",
        "Never merge it automatically",
        "require a preview and explicit confirmation",
        "A request to fix covers local fixes; committing and pushing them still need the user's explicit request",
    ),
    "rumo-handoff": (
        "Verify each fact now; do not copy it from memory.",
        "Never include passwords, tokens, keys, or private certificate material",
        "A handoff does not transfer approval for actions the user has not granted.",
        "## Tried And Dropped",
        "Copy the plan's decisions and dead ends",
        "never reads another project's",
        "Where they disagree, the repository wins; say so.",
        "Stop after the report unless the user asked to continue.",
        "Never repeat credentials that appear in a record.",
        "Make the handoff discoverable without this conversation.",
    ),
    "rumo-interface": (
        "A search is discovery, not proof of absence.",
        '"JSON ignores unknown fields" is not compatibility',
        "Ship compatible readers before new writers.",
        "Age alone never proves something is safe to remove",
        "Never reinterpret old data silently.",
    ),
    "rumo-lifecycle-safety": (
        "Do not infer readiness from service presence",
        "Separate a caller timeout from cancellation of underlying work.",
        "Preserve the primary failure when cleanup also fails",
        "Never swallow an exception merely to make",
        "Make disposal safe after partial startup and safe when invoked more than once.",
    ),
    "rumo-plan": (
        "Mark tasks that need separate authorization",
        "A clarifying answer revises the plan; it is not approval.",
        "Do not mark a record implemented because code was drafted or unit tests passed",
        "never start the next task on top of a failing one",
        "never run two tasks in parallel when they touch the same files",
        "A decision record never authorizes database writes, deployments, or other controlled actions.",
        "append one line for each fork, failure, or change of direction",
        "never edit or delete an earlier line",
    ),
    "rumo-reflect": (
        "Then stop and wait.",
        "Apply only items the user explicitly accepts",
        "never open issues, tickets, or notes on your own",
        "Do not invent lessons to fill the table.",
        "Remove the cause with structure",
        "say why each higher level cannot hold it",
        "run it against the real mistake from this session and confirm that it fails",
    ),
    "rumo-project-profile": (
        "It never prints credential values.",
        "Never guess when multiple profiles match.",
        "never copy them into the skills repository",
    ),
    "rumo-prose": (
        "Cut words only after every fact they carried survives somewhere.",
        "A review or audit reports findings",
        "Edit generated text at its source.",
        "Prompts, API errors, and product strings are behavior",
    ),
    "rumo-remote-ops": (
        "A successful connection is not authority.",
        "never read or copy private keys to get access working",
        "production needs authorization for the exact action and otherwise stays read-only",
        "A timeout, dropped connection, or accepted input does not mean failure or success.",
        "Never widen privileges, targets, deletion scope, or network access to force progress.",
    ),
    "rumo-review": (
        "do not edit code in review mode",
        "Review (default), Panel, and Simplify modes never edit code; only Loop and Respond do, and only on an explicit request.",
        "If its conditions hold, end the report with the one-line proposal it describes; launch nothing from here.",
        "Do not post replies, resolve threads, or request another review on the hosting platform unless the user asks.",
        "Do not guess the base from branch names.",
        "For a diff, report only issues this change introduces or materially exposes",
        "For a named-scope audit, report existing actionable issues inside that scope",
        "A guarantee you cannot see elsewhere is an open question attached to the finding, not a reason to withhold it.",
        "Each finding names the repository, file and line, the consequence, the triggering condition, and the evidence.",
        "Nothing is sent to another model or CLI until the user agrees",
    ),
    "rumo-test": (
        "watch it fail because the behavior is missing",
        "Never edit the implementation and its assertion together to manufacture a pass.",
        "A test that skips itself in a missing environment is not evidence that the environment passed.",
        "Do not mock the unit under test, weaken a meaningful assertion, or lower a threshold to get green.",
    ),
    "rumo-verify": (
        'No claim of "done", "fixed", or "passing" without fresh evidence',
        "Never stage, stash, reset, clean, or rewrite unrelated work",
        "never mark it passed",
        "those are separate authorizations",
        "Controlled actions you did not take, such as commits, pushes, or publication, are not verification gaps",
        "look for the project's verification recipe",
        "report the drift instead of following stale steps",
    ),
    "rumo-agent-collaboration": (
        "This skill governs only the agents it starts;",
        "Before declaring native subagents available or unavailable, read [references/native.md](references/native.md).",
        "Never start an agent through this skill unless the user asked for it.",
        "state in one line before launching which CLI, model, and effort will run and what content you will send",
        "A configured `delegate` lane counts as a named CLI.",
        "Ask first when the user named no route and none is configured, when you would send content the user did not mention, or when the work needs more access than the request implies.",
        "Exit 3 means nothing is configured: ask, and mention that `rumo-setup` saves the choice.",
        "the request approves shell access for that work",
        "Shell access the work does not need, such as shell for a review, needs its own approval; ask at most once per launch.",
        "A worktree is not a sandbox.",
        "never switch to automatic approval to finish.",
        "do not transfer ownership without a resumable session.",
        "Reviews by another model, including a named external CLI, belong to rumo-review alone: its panel runs them with this skill's scripts.",
        "a CLI without a confirmed read-only mode cannot have an adapter.",
        "Do not describe an adapter as tested end to end unless its `verified.live_run` is true.",
        "Otherwise add `--detach` to `start`, or after `open` wait for the user.",
        "Do not launch a disabled adapter, including the bundled Gemini and OpenCode declarations.",
        "Never give the receiver more access than you have, and never pass a flag that bypasses its sandbox, approvals, or tool limits.",
        "Do not switch route, model, or access level on your own.",
        "When you cannot tell whether a turn was delivered, check the recorded session before sending anything again.",
        "only when the user says this session should step away",
        "treat any request to hand work to another agent as delegation, whatever verb it uses",
        "Keep it to that line; do not ask again.",
        "`start` checks the CLI itself and runs without a window; `watch` shows its progress.",
        "Work that edits files or runs commands goes to an Orca terminal when Orca is installed",
        "When the CLI has no interactive template, use `start` and say why.",
        "Use `workspace-write` only where the adapter documents a directory restriction.",
        "each step names the next owner",
        "`open` returns once the window opens, not when the work is done.",
        "or in your report for Orca and native routes.",
        "Leave the full report for acceptance.",
        "get the report by resuming the session headlessly",
        "Client-specific (Claude Code):",
        "Tell the user and end your turn.",
        "rely on that report, not on the user;",
        "where the receiver runs, where the result will be, and what to tell you when it finishes",
        "do not read its events, logs, or session files and do not post progress updates.",
        "When the user reports that the receiver finished, read its result and check the working tree before accepting it.",
        "then stop changing that task.",
        "Cancel only runs this task started; never stop a process the record cannot prove is yours.",
    ),
    "rumo-setup": (
        "change only the items the user names. Never offer a reset to the defaults.",
        "Probe the new or changed lanes before writing",
        "do not look IDs up in the CLI's model catalog or configuration files",
        "write nothing for the roles that use it.",
        "Do not sign in to a CLI, change its configuration, or switch to another model or provider to make a probe pass",
        "Never put an API key, token, or password in the configuration",
        "do not edit the JSON by hand to get around it.",
        "Do not write defaults the user has not seen",
        "Never show lane syntax to the user",
        "When no other supported CLI is installed, say that no setup is needed",
    ),
}
PINNED_ELSEWHERE = {"rumo-clarify"}

# The same kind of rule, where it lives in a reference file the skill loads on
# demand. rumo-test/references/high-assurance.md and rumo-review/references/loop.md
# are pinned in test_skill_boundaries.py.
REFERENCE_RULES = {
    "rumo-remote-ops/references/access-changes-and-recovery.md": (
        "preserving the old route until independent validation succeeds",
        "Close the old route only after the new route is verified",
        "keep an existing authorized administration path until the new account and privileges are verified",
        "Stop further changes when validation fails or access is uncertain.",
    ),
    "rumo-remote-ops/references/connection-and-execution.md": (
        "do not delete known-host entries or use `StrictHostKeyChecking=no` to silence the event",
        "Do not replay migrations, restore jobs, file transfers with destructive options, or restarts just because the wrapper command failed.",
    ),
    "rumo-remote-ops/references/restore-and-verification.md": (
        "Require explicit authorization for that scope before writing.",
        "stop the restore mutation and report the missing prerequisite",
        "do not retry against a broader directory or another database",
    ),
    "rumo-remote-ops/references/deployment-and-acceptance.md": (
        "Do not use `docker compose down -v`, prune volumes, or grant privileged mode/host mounts to resolve a deployment failure without the corresponding explicit scope.",
    ),
    "rumo-remote-ops/references/upgrade-rollback-and-removal.md": (
        "Never weaken health checks or fabricate successful data to finish acceptance.",
        "Preserve configuration, persistent data, and credentials by default.",
    ),
    "rumo-remote-ops/references/service-deploy.md": (
        "Execute rollback only when already authorized, applicable to current state, and safe for data created since deployment",
    ),
    "rumo-interface/references/http.md": (
        "never hide an unchecked dimension behind a combined idempotency failure mark",
    ),
    "rumo-database-change-safety/references/procedure.md": (
        "Do not improvise a repair on the live target.",
    ),
    "rumo-frontend/references/browser-evidence.md": (
        "Do not commit, push, upload, edit a merge request, or publish to an asset branch unless the user explicitly requests that external action.",
    ),
    "rumo-frontend/references/dev-server.md": (
        "Never silently point a development server at an environment whose purpose is unclear.",
    ),
    "rumo-plan/references/parallel-execution.md": (
        "Stop on a conflict and ask; do not resolve it silently.",
    ),
    "rumo-coding-guidelines/references/task-flows.md": (
        "**Small edit.**",
        "**Defect fix.**",
        "**Feature.**",
        "**Investigation.**",
        "**Resume.**",
        "**Refactor.**",
        "Never claim it got faster without a measurement taken the same way before and after.",
        "If you cannot name the decision, it is not a prototype; use the feature flow.",
        "Prototype code never enters the product",
        "This flow ends with a diagnosis; a fix needs its own request.",
        "Never loosen the target to declare success.",
        "Never edit the baseline or the comparison tool to make a diff pass",
        "Never merge the pull request or mark it ready.",
        "Leave the changes as they are; commit only when the user asks.",
    ),
    "rumo-verify/references/recipe.md": (
        "Ask the user when you cannot tell whether the repository accepts committed agent files.",
        "Do not share a recipe between clients through a symbolic link",
        "Write every command relative to the repository root",
        "Until the recipe has run end to end, it is a draft.",
        "Stop only processes this run started; never stop a process by name.",
        "Cleanup never deletes the evidence.",
        "A product defect found during maintenance is reported, never written around in the recipe.",
    ),
    "rumo-review/references/codex-app-server.md": (
        "Do not let the script apply fixes.",
    ),
    "rumo-review/references/loop.md": (
        "never hard-code a provider",
        "One agreement covers later cycles on the same lane and content scope",
        "Withhold the fix history and earlier findings",
        "never substitute another provider or start a panel to keep the loop going",
    ),
    "rumo-plan/references/design-panel.md": (
        "The panel produces designs only, never code, and the plan is not broken into tasks until the user picks one.",
        "save it before reading any lane's draft.",
        "Withhold your own leaning and any option you already prefer.",
        "Do not propose one for a choice with one obvious shape or a local change.",
        "break the work down only after the user picks.",
    ),
    "rumo-review/references/panel.md": (
        "Never start another CLI on your own.",
        "Otherwise run only after the user agrees to those lanes and that content.",
        "A request that names the panel or the CLI, the review target, and the scope already supplies agreement; do not ask again for the same scope.",
        "Unverified status alone does not require repeated approval.",
        "without a confirmed read-only setting, do not use that CLI.",
        "A dropout is not evidence that the change has no findings.",
        "Never retry it on another model or substitute a close one, and never sign in, copy credentials, or change a CLI's configuration on the user's behalf.",
        "save your findings to a file before reading any lane's output.",
        "Withhold the fix history, earlier findings, and your own conclusions.",
        "launch with `--detach` instead, finish your own review, end your turn",
        "Do not propose one for small or low-risk changes, or when tests and evidence already settle the question.",
        "say in one sentence which of those conditions makes this change worth another model's view",
        "Propose at most once per target; after the user declines, do not raise it again until the target changes.",
        "the panel never edits code.",
    ),
    "rumo-review/references/judging-findings.md": (
        "Security, data-loss, and correctness findings get a full check even when only one reviewer raised them",
    ),
    "rumo-git-commit/references/pr-checks.md": (
        "A request to watch only reports results: no reruns, edits, commits, or pushes.",
        "otherwise stop after local verification and report what is ready to push",
        "Never edit an assertion only to make it pass, skip hooks, mark a required check optional, or disable a test to get green.",
        "Rerun that job once; a second failure makes it a real failure.",
        "stop and report instead of overwriting",
    ),
    "rumo-debug/references/remote-investigation.md": (
        "Choose process, listener, or container queries only when the symptom requires them.",
        "Stop and report the boundary when the environment purpose is unclear, credentials are unavailable, a query would require writes",
    ),
    "rumo-agent-collaboration/references/adapters.md": (
        "Approval that the headless turn cannot collect is a blocker, not permission to change modes.",
        "Constructed samples and mock tests establish parser/rendering behavior only.",
        "A disabled adapter cannot start or resume a turn, including a run saved before it was disabled.",
    ),
    "rumo-agent-collaboration/references/records.md": (
        "Do not paste tokens or keys into a brief; name where they live instead.",
        "do not resume it as a writer unless the user hands it back.",
        "Unknown identity is not proof that a process has exited.",
    ),
    "rumo-agent-collaboration/references/native.md": (
        "Do not infer availability from the CLI name, version, or an installed package alone.",
        "Check child permissions separately; parent read-only access does not prove child read-only access.",
        "Inspect the current tool list first, then extension loading and registration, then invocation flags and permissions; consult local help or implementation only for remaining gaps.",
        "Report one of: available, installed but not loaded, disabled for this invocation, confirmed absent, or unconfirmed.",
        "Starting a subagent does not prove background survival or completion notification.",
        "Verify the child's tools, permissions, model, and provider separately from the parent's.",
        "Distinguish turn completion, session switching, and parent process exit.",
        "When child read-only access cannot be established, use an already authorized read-only route or report the blocker.",
        "Do not enable shell tools, extensions, or wider approvals to make a route available.",
        "| Extension registered and allowed; start tool exposed | Available for starting; check other capabilities separately. |",
        "| Package installed; tool missing; loading not checked | Unconfirmed; check loading, do not declare absence. |",
        "| Package installed; runtime confirms it was not loaded | Installed but not loaded. |",
        "| Invocation disables the extension or denies the tool | Disabled for this invocation. |",
        "| Current runtime confirms no built-in or extension implementation | Confirmed absent. |",
        "| Parent allows only reads; child tool policy is unknown | Child read-only access is unconfirmed; use a verified route or stop. |",
        "| Parent turn ended; process still alive | Check cross-turn survival and notification; do not infer process exit. |",
    ),
    "rumo-agent-collaboration/references/orca.md": (
        "end your turn as Workflow step 4 in SKILL.md allows",
    ),
    "rumo-agent-collaboration/references/external-cli.md": (
        "More than one listed match for a fragment: ask the user which one.",
        "`start` and `open` check the CLI and the adapter's flags themselves, so do not run `list`, `check`, or `show` first for a verified adapter.",
        "run `agent_run.py show` and show the user the full command and known limits",
        "Unverified status alone does not require repeated approval.",
        "Official documentation may establish a write mode while `verified` stays null",
        "The bundled pi adapter intentionally disables MCP and extension discovery with `--no-mcp` and `--no-extensions`.",
        "An installed subagent package does not make its tools available in that invocation.",
        "Keep the adapter's restrictions; do not remove them or add shell access to recover subagents.",
    ),
}

# Optional skills under extras/ whose rules guard the user's authority.
EXTRA_RULES: dict[str, tuple[str, ...]] = {
    "rumo-offline-delivery-audit": (
        "A review or audit is static and read-only by default",
        "never substitute static inspection for installation evidence",
    ),
}
EXTRA_REFERENCE_RULES: dict[str, tuple[str, ...]] = {
    "rumo-diagram/references/mermaid.md": (
        "get the user's agreement before installing it",
        "stop before PNG export",
    ),
    "rumo-linux-inspect/references/hardware-inventory.md": (
        "generating the two new files does not authorize deleting it",
        "follow `rumo-filesystem-safety`",
    ),
}

# Each always-on snippet bullet must restate a rule a skill already owns, so the
# pasted copy cannot grow rules of its own. Keys match the bullet; values are
# (skill, phrase in that skill's body).
SNIPPET = REPO_ROOT / "skills" / "rumo-coding-guidelines" / "references" / "agents-snippet.md"
SNIPPET_SOURCES = {
    "Read the real entry point and call chain": ("rumo-coding-guidelines", "Find the real entry point, call chain"),
    "repository instructions override these defaults": ("rumo-coding-guidelines", "follow them over these defaults"),
    "report unrelated problems instead of fixing them": ("rumo-coding-guidelines", "Report unrelated problems you notice instead of fixing them."),
    "No speculative abstractions, drive-by refactors": ("rumo-coding-guidelines", "Do not reformat, rename, reorder, or refactor neighboring code."),
    "load rumo-test and apply its risk gate": ("rumo-coding-guidelines", "load the `rumo-test` skill and apply its high-assurance risk gate before editing"),
    "use rumo-verify before handing back": ("rumo-coding-guidelines", "Use `rumo-verify` before claiming the change is ready."),
    "offer once to review the session": ("rumo-coding-guidelines", "end with a one-line offer to review the session for lessons, at most once per session"),
}
SNIPPET_INDEX_PREFIXES = ("- Flow:", "- Full rules:")


def normalized_body(skill: str) -> str:
    text = (REPO_ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return " ".join(text.split("\n---\n", 1)[1].split())


class SkillRulesTest(unittest.TestCase):
    def test_every_default_skill_pins_rules(self) -> None:
        skills = {path.parent.name for path in (REPO_ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual(sorted(skills - PINNED_ELSEWHERE - RULES.keys()), [])
        self.assertEqual(sorted(RULES.keys() - skills), [])

    def test_pinned_rules_remain_in_body(self) -> None:
        for skill, rules in RULES.items():
            body = normalized_body(skill)
            for rule in rules:
                with self.subTest(skill=skill, rule=rule):
                    self.assertTrue(rule in body, f"{skill}: pinned rule missing from SKILL.md body")

    def test_pinned_reference_rules_remain(self) -> None:
        for reference, rules in REFERENCE_RULES.items():
            text = " ".join((REPO_ROOT / "skills" / reference).read_text(encoding="utf-8").split())
            for rule in rules:
                with self.subTest(reference=reference, rule=rule):
                    self.assertTrue(rule in text, f"{reference}: pinned rule missing")

    def test_pinned_extra_rules_remain(self) -> None:
        for skill, rules in EXTRA_RULES.items():
            text = " ".join((REPO_ROOT / "extras" / skill / "SKILL.md").read_text(encoding="utf-8").split())
            for rule in rules:
                with self.subTest(skill=skill, rule=rule):
                    self.assertTrue(rule in text, f"{skill}: pinned rule missing")
        for reference, rules in EXTRA_REFERENCE_RULES.items():
            text = " ".join((REPO_ROOT / "extras" / reference).read_text(encoding="utf-8").split())
            for rule in rules:
                with self.subTest(reference=reference, rule=rule):
                    self.assertTrue(rule in text, f"{reference}: pinned rule missing")


class AlwaysOnSnippetTest(unittest.TestCase):
    def bullets(self) -> list[str]:
        block = SNIPPET.read_text(encoding="utf-8").split("```markdown\n", 1)[1].split("```", 1)[0]
        return [line for line in block.splitlines() if line.startswith("- ")]

    def test_every_bullet_restates_an_owned_rule(self) -> None:
        for bullet in self.bullets():
            with self.subTest(bullet=bullet):
                if bullet.startswith(SNIPPET_INDEX_PREFIXES):
                    continue
                sources = [value for key, value in SNIPPET_SOURCES.items() if key in bullet]
                self.assertTrue(sources, "snippet bullet has no owning rule in SNIPPET_SOURCES")
                for skill, phrase in sources:
                    self.assertTrue(phrase in normalized_body(skill), f"{skill}: snippet source phrase missing")

    def test_every_source_is_used(self) -> None:
        text = " ".join(self.bullets())
        for key in SNIPPET_SOURCES:
            with self.subTest(key=key):
                self.assertIn(key, text)

    def test_index_names_existing_default_skills(self) -> None:
        names = set(re.findall(r"rumo-[a-z-]+[a-z]", " ".join(self.bullets())))
        self.assertTrue(names)
        for name in sorted(names):
            with self.subTest(skill=name):
                self.assertTrue((REPO_ROOT / "skills" / name / "SKILL.md").is_file())


# The installer edits users' own instruction files only on request; an agent
# installing from the README must ask first.
README_INSTALL_RULES = {
    "README.md": (
        "--dry-run",
        "写入我的用户级 CLAUDE.md 或 AGENTS.md 之前先问我",
        "没有用户明确同意，绝不加 `--baseline` 或 `-Baseline`",
    ),
    "README.en.md": (
        "--dry-run",
        "Ask me before writing to my user-level CLAUDE.md or AGENTS.md.",
        "it never adds `--baseline` or `-Baseline` without the user's explicit agreement",
    ),
}


class ReadmeInstallRulesTest(unittest.TestCase):
    def test_agent_install_asks_before_baseline(self) -> None:
        for name, rules in README_INSTALL_RULES.items():
            text = (REPO_ROOT / name).read_text(encoding="utf-8")
            for rule in rules:
                with self.subTest(readme=name, rule=rule):
                    self.assertTrue(rule in text, f"{name}: agent install rule missing")


# A skill change that alters triggering or behavior is accepted in a real client
# before push; validators only prove the files are well formed.
ACCEPTANCE_RULES = {
    "CONTRIBUTING.md": (
        "### Acceptance before push",
        "alters a skill's `description` or a rule that decides what the agent does",
        "record the candidate commit, client and version, model, cases, results, and evidence directory",
        "Never report such a change ready to push without this run",
    ),
    "AGENTS.md": (
        "run the acceptance in `CONTRIBUTING.md`",
    ),
}


class AcceptanceRulesTest(unittest.TestCase):
    def test_skill_changes_need_real_client_acceptance(self) -> None:
        for name, rules in ACCEPTANCE_RULES.items():
            text = " ".join((REPO_ROOT / name).read_text(encoding="utf-8").split())
            for rule in rules:
                with self.subTest(file=name, rule=rule):
                    self.assertTrue(rule in text, f"{name}: acceptance rule missing")


if __name__ == "__main__":
    unittest.main()
