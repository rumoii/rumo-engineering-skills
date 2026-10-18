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
        "Open or update a pull request only when the user asks.",
        "Never merge it automatically",
        "require a preview and explicit confirmation",
    ),
    "rumo-handoff": (
        "Verify each fact now; do not copy it from memory.",
        "Never include passwords, tokens, keys, or private certificate material",
        "A handoff does not transfer approval for actions the user has not granted.",
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
        "Review (default) and Simplify modes never edit code; only Loop and Respond do, and only on an explicit request.",
        "Do not post replies, resolve threads, or request another review on the hosting platform unless the user asks.",
        "Do not guess the base from branch names.",
        "For a diff, report only issues this change introduces or materially exposes",
        "For a named-scope audit, report existing actionable issues inside that scope",
        "A guarantee you cannot see elsewhere is an open question attached to the finding, not a reason to withhold it.",
        "Each finding names the repository, file and line, the consequence, the triggering condition, and the evidence.",
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
    "rumo-review/references/codex-app-server.md": (
        "Do not let the script apply fixes.",
    ),
    "rumo-debug/references/remote-investigation.md": (
        "Choose process, listener, or container queries only when the symptom requires them.",
        "Stop and report the boundary when the environment purpose is unclear, credentials are unavailable, a query would require writes",
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


if __name__ == "__main__":
    unittest.main()
