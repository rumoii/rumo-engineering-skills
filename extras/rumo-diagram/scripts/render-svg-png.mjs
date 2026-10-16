#!/usr/bin/env node

import { existsSync } from "node:fs";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";

function usage() {
  console.log(`render-svg-png.mjs

Usage:
  node render-svg-png.mjs --svg <file> --out <png> [--browser <path>]
`);
}

function parseArgs(argv) {
  const args = { svg: "", out: "", browser: "" };
  for (let index = 2; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--help" || value === "-h") {
      args.help = true;
    } else if (["--svg", "--out", "--browser"].includes(value) && argv[index + 1]) {
      args[value.slice(2)] = argv[index + 1];
      index += 1;
    } else {
      throw new Error(`Unknown or incomplete argument: ${value}`);
    }
  }
  return args;
}

function browserCandidates(explicitPath) {
  if (explicitPath) return [explicitPath];
  if (process.env.CHROME_PATH) return [process.env.CHROME_PATH];
  if (process.platform === "win32") {
    const programFiles = process.env.PROGRAMFILES || "C:\\Program Files";
    const programFilesX86 = process.env["PROGRAMFILES(X86)"] || "C:\\Program Files (x86)";
    const localAppData = process.env.LOCALAPPDATA || "";
    return [
      join(programFiles, "Google", "Chrome", "Application", "chrome.exe"),
      join(programFilesX86, "Google", "Chrome", "Application", "chrome.exe"),
      join(localAppData, "Google", "Chrome", "Application", "chrome.exe"),
      join(programFiles, "Microsoft", "Edge", "Application", "msedge.exe"),
      join(programFilesX86, "Microsoft", "Edge", "Application", "msedge.exe"),
    ];
  }
  if (process.platform === "darwin") {
    return [
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
      "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ];
  }
  return [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ];
}

function findBrowser(explicitPath) {
  return browserCandidates(explicitPath).find(candidate => candidate && existsSync(candidate)) || "";
}

function parseCanvas(svg) {
  const opening = svg.match(/<svg\b[^>]*>/i)?.[0] || "";
  const width = Number(opening.match(/\bwidth=["']([0-9.]+)["']/i)?.[1]);
  const height = Number(opening.match(/\bheight=["']([0-9.]+)["']/i)?.[1]);
  if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1) {
    throw new Error("SVG must declare positive integer width and height attributes");
  }
  return { width, height };
}

function readPngSize(buffer) {
  const signature = "89504e470d0a1a0a";
  if (buffer.length < 24 || buffer.subarray(0, 8).toString("hex") !== signature) {
    throw new Error("Browser output is not a valid PNG file");
  }
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    usage();
    return;
  }
  if (!args.svg || !args.out) {
    usage();
    throw new Error("--svg and --out are required");
  }

  const svgPath = resolve(args.svg);
  const outPath = resolve(args.out);
  const svg = await readFile(svgPath, "utf8");
  const { width, height } = parseCanvas(svg);
  const browser = findBrowser(args.browser);
  if (!browser) {
    throw new Error("Cannot find Chrome, Edge, or Chromium. Pass --browser or set CHROME_PATH");
  }

  const workDir = await mkdtemp(join(tmpdir(), "rumo-topology-render-"));
  const profileDir = join(workDir, "profile");
  const htmlPath = join(workDir, "render.html");
  const escapedSvg = svg.replace(/<\/script>/gi, "<\\/script>");
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>*{box-sizing:border-box}html,body{margin:0;width:${width}px;height:${height}px;overflow:hidden;background:#fff}svg{display:block;width:${width}px;height:${height}px}</style></head><body>${escapedSvg}</body></html>`;

  try {
    await writeFile(htmlPath, html, "utf8");
    const result = spawnSync(browser, [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--no-default-browser-check",
      `--user-data-dir=${profileDir}`,
      `--window-size=${width},${height}`,
      `--screenshot=${outPath}`,
      pathToFileURL(htmlPath).href,
    ], { encoding: "utf8", timeout: 120000 });
    if (result.error) throw result.error;
    if (result.status !== 0 || !existsSync(outPath)) {
      throw new Error(`Browser rendering failed (${result.status}): ${(result.stderr || result.stdout).trim()}`);
    }
    const png = await readFile(outPath);
    const actual = readPngSize(png);
    if (actual.width !== width || actual.height !== height) {
      throw new Error(`PNG dimensions ${actual.width}x${actual.height} do not match SVG ${width}x${height}`);
    }
    console.log(`Rendered ${basename(svgPath)} -> ${outPath} (${width}x${height})`);
  } finally {
    await rm(workDir, { recursive: true, force: true });
  }
}

main().catch(error => {
  console.error(error.message || error);
  process.exit(1);
});
