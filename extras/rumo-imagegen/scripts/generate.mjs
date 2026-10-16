#!/usr/bin/env node

import { createHash } from "node:crypto";
import { existsSync, linkSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const API_ENDPOINT = process.env.RUMO_IMAGE_ENDPOINT?.trim() ?? "";
const DEFAULT_MODEL = process.env.RUMO_IMAGE_MODEL?.trim() || "gpt-image-1";
const DEFAULT_SIZE = process.env.RUMO_IMAGE_SIZE?.trim() || "1024x1024";
const DEFAULT_QUALITY = process.env.RUMO_IMAGE_QUALITY?.trim() || "high";
const DEFAULT_TIMEOUT_MS = 600_000;

function usage() {
  return `Usage:
  generate.mjs --dry-run --prompt-file <path> --output <path.png>
  generate.mjs --allow-insecure-http --prompt-file <path> --output <path.png>

Options:
  --allow-insecure-http  Acknowledge that the bearer token and prompt use plain HTTP
  --dry-run              Validate without reading RUMO_IMAGE_API_KEY or calling the API
  --endpoint <url>       Default: RUMO_IMAGE_ENDPOINT
  --model <name>         Default: RUMO_IMAGE_MODEL or gpt-image-1
  --output <path>        Required local output path; existing files are not overwritten
  --prompt-file <path>   Required UTF-8 prompt file
  --quality <value>      Default: high
  --size <WxH>           Default: 1024x1024
  --timeout-ms <number>  Default: 600000
  --help                 Show this help`;
}

export function parseArgs(argv) {
  const options = {
    allowInsecureHttp: false,
    dryRun: false,
    endpoint: API_ENDPOINT,
    model: DEFAULT_MODEL,
    output: null,
    promptFile: null,
    quality: DEFAULT_QUALITY,
    size: DEFAULT_SIZE,
    timeoutMs: DEFAULT_TIMEOUT_MS,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--allow-insecure-http") {
      options.allowInsecureHttp = true;
    } else if (argument === "--dry-run") {
      options.dryRun = true;
    } else if (argument === "--help" || argument === "-h") {
      options.help = true;
    } else if (["--endpoint", "--model", "--output", "--prompt-file", "--quality", "--size", "--timeout-ms"].includes(argument)) {
      const value = argv[index + 1];
      if (!value) throw new Error(`${argument} requires a value`);
      index += 1;
      if (argument === "--endpoint") options.endpoint = value;
      if (argument === "--model") options.model = value;
      if (argument === "--output") options.output = value;
      if (argument === "--prompt-file") options.promptFile = value;
      if (argument === "--quality") options.quality = value;
      if (argument === "--size") options.size = value;
      if (argument === "--timeout-ms") options.timeoutMs = Number(value);
    } else {
      throw new Error(`Unknown argument: ${argument}`);
    }
  }

  return options;
}

function validateSize(size) {
  const match = /^(\d+)x(\d+)$/.exec(size);
  if (!match) throw new Error("Size must use WIDTHxHEIGHT, for example 1024x1024");
  const width = Number(match[1]);
  const height = Number(match[2]);
  if (width < 1 || height < 1 || width > 4096 || height > 4096) {
    throw new Error("Image dimensions must be between 1 and 4096 pixels");
  }
}

export function buildPlan(options) {
  if (!options.endpoint) throw new Error("Provide --endpoint or set RUMO_IMAGE_ENDPOINT");
  if (!options.promptFile) throw new Error("--prompt-file is required");
  if (!options.output) throw new Error("--output is required");
  if (!options.model.trim()) throw new Error("Model must not be empty");
  if (!options.quality.trim()) throw new Error("Quality must not be empty");
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < 1) {
    throw new Error("Timeout must be a positive integer");
  }
  validateSize(options.size);

  const promptFile = path.resolve(options.promptFile);
  const output = path.resolve(options.output);
  const promptStat = statSync(promptFile);
  if (!promptStat.isFile()) throw new Error(`Prompt path is not a regular file: ${promptFile}`);
  if (existsSync(output)) throw new Error(`Output already exists: ${output}`);
  const outputParent = path.dirname(output);
  if (!statSync(outputParent).isDirectory()) throw new Error(`Output parent is not a directory: ${outputParent}`);

  const prompt = readFileSync(promptFile, "utf8").trim();
  if (!prompt) throw new Error("Prompt file is empty");
  if ([...prompt].length > 100_000) throw new Error("Prompt exceeds the 100000-character safety limit");
  if (!options.dryRun && options.endpoint.startsWith("http://") && !options.allowInsecureHttp) {
    throw new Error(
      "Plain HTTP is not acknowledged; add --allow-insecure-http only after accepting the transport risk",
    );
  }

  return {
    endpoint: options.endpoint,
    model: options.model,
    output,
    prompt,
    promptChars: [...prompt].length,
    promptSha256: createHash("sha256").update(prompt).digest("hex"),
    quality: options.quality,
    size: options.size,
    timeoutMs: options.timeoutMs,
  };
}

function redactedError(body, apiKey) {
  return body.replaceAll(apiKey, "[REDACTED]").slice(0, 1000);
}

function imageFormat(bytes) {
  if (bytes.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))) {
    return "png";
  }
  if (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) return "jpeg";
  if (bytes.subarray(0, 6).toString("ascii") === "GIF87a" || bytes.subarray(0, 6).toString("ascii") === "GIF89a") {
    return "gif";
  }
  if (bytes.subarray(0, 4).toString("ascii") === "RIFF" && bytes.subarray(8, 12).toString("ascii") === "WEBP") {
    return "webp";
  }
  throw new Error("API response is not a recognized PNG, JPEG, GIF, or WebP image");
}

function validateOutputFormat(output, format) {
  const extension = path.extname(output).toLowerCase();
  const allowed = {
    gif: [".gif"],
    jpeg: [".jpeg", ".jpg"],
    png: [".png"],
    webp: [".webp"],
  }[format];
  if (!allowed.includes(extension)) {
    throw new Error(`Output extension ${extension || "(none)"} does not match returned ${format} image data`);
  }
}

async function responseBytes(item, timeoutMs, fetchImpl) {
  if (typeof item?.b64_json === "string" && item.b64_json.length > 0) {
    const bytes = Buffer.from(item.b64_json, "base64");
    if (bytes.length === 0) throw new Error("API returned empty base64 image data");
    return { bytes, source: "b64_json" };
  }

  if (typeof item?.url === "string" && item.url.startsWith("data:image/")) {
    const match = /^data:image\/[^;]+;base64,(.+)$/s.exec(item.url);
    if (!match) throw new Error("API returned an unsupported image data URL");
    const bytes = Buffer.from(match[1], "base64");
    if (bytes.length === 0) throw new Error("API returned an empty image data URL");
    return { bytes, source: "data_url" };
  }

  if (typeof item?.url === "string") {
    const imageUrl = new URL(item.url);
    if (imageUrl.protocol !== "https:" && imageUrl.protocol !== "http:") {
      throw new Error(`API returned an unsupported image URL protocol: ${imageUrl.protocol}`);
    }
    const response = await fetchImpl(imageUrl, { signal: AbortSignal.timeout(timeoutMs) });
    if (!response.ok) throw new Error(`Image download failed with HTTP ${response.status}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    if (bytes.length === 0) throw new Error("Downloaded image is empty");
    return { bytes, source: "url" };
  }

  throw new Error("API response does not contain data[0].b64_json or data[0].url");
}

export async function generateImage(plan, apiKey, fetchImpl = fetch) {
  const response = await fetchImpl(plan.endpoint, {
    body: JSON.stringify({
      model: plan.model,
      n: 1,
      prompt: plan.prompt,
      quality: plan.quality,
      size: plan.size,
    }),
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    method: "POST",
    redirect: "error",
    signal: AbortSignal.timeout(plan.timeoutMs),
  });
  const body = await response.text();
  if (!response.ok) throw new Error(`Image API HTTP ${response.status}: ${redactedError(body, apiKey)}`);

  let payload;
  try {
    payload = JSON.parse(body);
  } catch {
    throw new Error("Image API returned invalid JSON");
  }
  const image = await responseBytes(payload?.data?.[0], plan.timeoutMs, fetchImpl);
  const format = imageFormat(image.bytes);
  validateOutputFormat(plan.output, format);

  const temporaryOutput = path.join(path.dirname(plan.output), `.${path.basename(plan.output)}.${process.pid}.tmp`);
  try {
    writeFileSync(temporaryOutput, image.bytes, { flag: "wx", mode: 0o600 });
    linkSync(temporaryOutput, plan.output);
    rmSync(temporaryOutput);
  } catch (error) {
    rmSync(temporaryOutput, { force: true });
    throw error;
  }

  return {
    bytes: image.bytes.length,
    format,
    model: plan.model,
    output: plan.output,
    quality: plan.quality,
    size: plan.size,
    source: image.source,
  };
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  if (options.help) {
    process.stdout.write(`${usage()}\n`);
    return;
  }

  const plan = buildPlan(options);
  if (options.dryRun) {
    const { prompt: _prompt, ...safePlan } = plan;
    process.stdout.write(`${JSON.stringify(safePlan, null, 2)}\n`);
    return;
  }

  const apiKey = process.env.RUMO_IMAGE_API_KEY?.trim();
  if (!apiKey) throw new Error("RUMO_IMAGE_API_KEY is not available in this process environment");
  const result = await generateImage(plan, apiKey);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1]);
if (isMain) {
  main().catch((error) => {
    process.stderr.write(`rumo-imagegen: ${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
