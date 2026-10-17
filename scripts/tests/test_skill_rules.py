from __future__ import annotations

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
        "After three hypotheses in a row are refuted, or after a fix leaves the symptom in place twice",
        "stays read-only unless the user authorizes the exact change",
        "Keep source reasoning separate from runtime proof.",
    ),
    "rumo-filesystem-safety": (
        "Use the light path only when every one of these holds",
        "Use the full path whenever any of these applies",
        "Do not traverse a link to delete its destination.",
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
        "Do not guess the base from branch names.",
        "Report only issues this change introduces or materially exposes",
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
    ),
}
PINNED_ELSEWHERE = {"rumo-clarify"}


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


if __name__ == "__main__":
    unittest.main()
