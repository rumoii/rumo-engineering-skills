// pi extension loaded by the pi eval runners. pi has no sandbox, so this keeps the
// read-only tools inside the sample workspace (pi's working directory) and blocks
// every other tool. A handler error also blocks the call in pi.
import { realpathSync } from "node:fs";
import os from "node:os";
import path from "node:path";

const READ_ONLY_TOOLS = new Set(["read", "grep", "find", "ls"]);
const GLOB_FIELDS = { find: "pattern", grep: "glob" };

function canonical(target) {
  try {
    return realpathSync.native(target);
  } catch {
    return target;
  }
}

// Mirrors pi's own resolution: a leading "@" is dropped, "~" is the home directory,
// and relative paths start from the working directory.
export function resolveTarget(value, root) {
  let target = value.startsWith("@") ? value.slice(1) : value;
  if (target === "~" || target.startsWith("~/") || target.startsWith("~\\")) {
    target = path.join(os.homedir(), target.slice(1));
  }
  return canonical(path.resolve(root, target));
}

export function isInside(root, target) {
  const fold = (value) => (process.platform === "win32" ? value.toLowerCase() : value);
  const relative = path.relative(fold(root), fold(target));
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function globEscapes(value) {
  return path.isAbsolute(value) || /^[A-Za-z]:/.test(value) || value.startsWith("~") || value.split(/[\\/]/).includes("..");
}

export function blockReason(toolName, input, root) {
  if (!READ_ONLY_TOOLS.has(toolName)) {
    return `${toolName} is not available here`;
  }
  const requested = typeof input?.path === "string" && input.path ? input.path : ".";
  if (!isInside(root, resolveTarget(requested, root))) {
    return `${requested} is outside the working directory`;
  }
  const field = GLOB_FIELDS[toolName];
  if (field && typeof input?.[field] === "string" && globEscapes(input[field])) {
    return `${field} reaches outside the working directory`;
  }
  return null;
}

export default function (pi) {
  const root = canonical(process.cwd());
  pi.on("tool_call", async (event) => {
    const reason = blockReason(event.toolName, event.input, root);
    return reason ? { block: true, reason } : undefined;
  });
}
