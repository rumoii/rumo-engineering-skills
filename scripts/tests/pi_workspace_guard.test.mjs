import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import guard, { blockReason } from "../pi_workspace_guard.mjs";

async function withWorkspace(run) {
  const parent = mkdtempSync(path.join(os.tmpdir(), "pi-guard-"));
  const root = path.join(parent, "project");
  mkdirSync(path.join(root, ".agents", "skills", "rumo-debug"), { recursive: true });
  writeFileSync(path.join(root, ".agents", "skills", "rumo-debug", "SKILL.md"), "---\nname: rumo-debug\n---\n");
  writeFileSync(path.join(parent, "outside.txt"), "private\n");
  try {
    return await run(root, parent);
  } finally {
    rmSync(parent, { force: true, recursive: true });
  }
}

test("paths inside the workspace pass, relative or absolute", async () => {
  await withWorkspace((root) => {
    const skill = path.join(root, ".agents", "skills", "rumo-debug", "SKILL.md");
    assert.equal(blockReason("read", { path: ".agents/skills/rumo-debug/SKILL.md" }, root), null);
    assert.equal(blockReason("read", { path: skill }, root), null);
    assert.equal(blockReason("read", { path: `@${skill}` }, root), null);
    assert.equal(blockReason("ls", {}, root), null);
    assert.equal(blockReason("grep", { pattern: "C:/Users", glob: "**/*.md" }, root), null);
    assert.equal(blockReason("find", { pattern: "src/**/*.ts", path: "." }, root), null);
  });
});

test("paths that leave the workspace are blocked", async () => {
  await withWorkspace((root, parent) => {
    for (const input of [
      { path: path.join(parent, "outside.txt") },
      { path: "../outside.txt" },
      { path: `@${parent}` },
      { path: "~" },
      { path: "~/.ssh/id_rsa" },
      { path: path.join(root, "..", "outside.txt") },
    ]) {
      assert.match(blockReason("read", input, root) ?? "", /outside the working directory/, JSON.stringify(input));
    }
    assert.match(blockReason("ls", { path: os.homedir() }, root) ?? "", /outside/);
  });
});

test("globs that reach outside the workspace are blocked", async () => {
  await withWorkspace((root) => {
    for (const pattern of ["/etc/*", "C:/Users/**", "../**/*.md", "~/.config/*", "src/../../x"]) {
      assert.match(blockReason("find", { pattern }, root) ?? "", /pattern reaches outside/, pattern);
    }
    assert.match(blockReason("grep", { pattern: "x", glob: "../*.md" }, root) ?? "", /glob reaches outside/);
  });
});

test("tools other than the read-only four are blocked", async () => {
  await withWorkspace((root) => {
    for (const tool of ["write", "edit", "bash", "powershell", "mcp__docs__read"]) {
      assert.match(blockReason(tool, { path: "a.txt" }, root) ?? "", /not available/);
    }
  });
});

test("the extension blocks through pi's tool_call hook from its working directory", async () => {
  await withWorkspace(async (root, parent) => {
    const handlers = {};
    const previous = process.cwd();
    process.chdir(root);
    try {
      guard({ on: (event, handler) => { handlers[event] = handler; } });
    } finally {
      process.chdir(previous);
    }
    assert.deepEqual(await handlers.tool_call({ toolName: "read", input: { path: "a.txt" } }), undefined);
    const blocked = await handlers.tool_call({ toolName: "ls", input: { path: parent } });
    assert.equal(blocked.block, true);
  });
});
