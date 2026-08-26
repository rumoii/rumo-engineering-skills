import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { buildPlan, generateImage, parseArgs } from "./generate.mjs";

function withTemporaryDirectory(run) {
  const directory = mkdtempSync(path.join(os.tmpdir(), "rumo-imagegen-test-"));
  try {
    const result = run(directory);
    if (result && typeof result.then === "function") {
      return result.finally(() => rmSync(directory, { force: true, recursive: true }));
    }
    rmSync(directory, { force: true, recursive: true });
    return result;
  } catch (error) {
    rmSync(directory, { force: true, recursive: true });
    throw error;
  }
}

test("parseArgs uses the documented defaults", () => {
  const options = parseArgs(["--dry-run", "--prompt-file", "prompt.txt", "--output", "result.png"]);

  assert.equal(options.dryRun, true);
  assert.equal(options.endpoint, "");
  assert.equal(options.model, "gpt-image-1");
  assert.equal(options.size, "1024x1024");
  assert.equal(options.quality, "high");
  assert.equal(options.timeoutMs, 600_000);
});

test("buildPlan validates a dry run without insecure transport acknowledgement", () => {
  withTemporaryDirectory((directory) => {
    const promptFile = path.join(directory, "prompt.txt");
    const output = path.join(directory, "result.png");
    writeFileSync(promptFile, "  a precise test prompt  ", { mode: 0o600 });

    const plan = buildPlan(parseArgs(["--dry-run", "--endpoint", "https://example.test/v1/images/generations", "--prompt-file", promptFile, "--output", output]));

    assert.equal(plan.prompt, "a precise test prompt");
    assert.equal(plan.promptChars, 21);
    assert.match(plan.promptSha256, /^[a-f0-9]{64}$/);
    assert.equal(plan.output, output);
  });
});

test("buildPlan rejects a live request without plain HTTP acknowledgement", () => {
  withTemporaryDirectory((directory) => {
    const promptFile = path.join(directory, "prompt.txt");
    const output = path.join(directory, "result.png");
    writeFileSync(promptFile, "test prompt", { mode: 0o600 });

    assert.throws(
      () => buildPlan(parseArgs(["--endpoint", "http://example.test/v1/images/generations", "--prompt-file", promptFile, "--output", output])),
      /Plain HTTP is not acknowledged/,
    );
  });
});

test("generateImage sends one request and atomically saves returned PNG data", async () => {
  await withTemporaryDirectory(async (directory) => {
    const output = path.join(directory, "result.png");
    const png = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x01]);
    let request;
    const fetchImpl = async (url, options) => {
      request = { options, url };
      return new Response(JSON.stringify({ data: [{ b64_json: png.toString("base64") }] }), {
        headers: { "Content-Type": "application/json" },
        status: 200,
      });
    };
    const plan = {
      endpoint: "http://example.test/v1/images/generations",
      model: "gpt-image-2",
      output,
      prompt: "test prompt",
      quality: "high",
      size: "1024x1024",
      timeoutMs: 1_000,
    };

    const result = await generateImage(plan, "secret-value", fetchImpl);

    assert.equal(request.url, plan.endpoint);
    assert.equal(request.options.method, "POST");
    assert.equal(request.options.headers.Authorization, "Bearer secret-value");
    assert.deepEqual(JSON.parse(request.options.body), {
      model: "gpt-image-2",
      n: 1,
      prompt: "test prompt",
      quality: "high",
      size: "1024x1024",
    });
    assert.deepEqual(readFileSync(output), png);
    assert.equal(result.source, "b64_json");
    assert.equal(result.format, "png");
  });
});

test("generateImage redacts the API key from an HTTP failure", async () => {
  await withTemporaryDirectory(async (directory) => {
    const plan = {
      endpoint: "http://example.test/v1/images/generations",
      model: "gpt-image-2",
      output: path.join(directory, "result.png"),
      prompt: "test prompt",
      quality: "high",
      size: "1024x1024",
      timeoutMs: 1_000,
    };
    const fetchImpl = async () => new Response("failure secret-value", { status: 401 });

    await assert.rejects(() => generateImage(plan, "secret-value", fetchImpl), /failure \[REDACTED\]/);
  });
});
