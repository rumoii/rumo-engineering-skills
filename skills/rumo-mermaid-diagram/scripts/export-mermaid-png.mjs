#!/usr/bin/env node
/**
 * Export a Mermaid flowchart preview page (or Markdown Mermaid block) to PNG.
 *
 * Usage:
 *   node export-mermaid-png.mjs --html docs/flow.html --out docs/flow.png [--scale 3]
 *   node export-mermaid-png.mjs --md docs/flow.md --out docs/flow.png [--title "标题"] [--scale 3]
 *
 * Env:
 *   CHROME_PATH          Optional Chrome/Chromium executable
 *   PLAYWRIGHT_CORE      Optional path to playwright-core index.mjs
 *
 * Cross-platform notes:
 *   - macOS/Linux: node export-mermaid-png.mjs ...
 *   - Windows: py is not required; use `node export-mermaid-png.mjs ...` from Git Bash or PowerShell
 */

import { createServer } from "node:http";
import { readFile, writeFile, mkdtemp, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join, extname, resolve, basename } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { tmpdir } from "node:os";
import { createRequire } from "node:module";

const __dirname = dirname(fileURLToPath(import.meta.url));
const skillRoot = join(__dirname, "..");
const defaultTemplate = join(skillRoot, "templates", "flow-preview.html");

function printHelp() {
  console.log(`export-mermaid-png.mjs

Options:
  --html <path>     Preview HTML page to export (contains Mermaid or loads .md)
  --md <path>       Markdown file with a \`\`\`mermaid fenced block
  --out <path>      Output PNG path (required)
  --title <text>    Title when using --md (optional)
  --hint <text>     Hint text when using --md (optional)
  --basename <name> Download basename override (optional)
  --scale <n>       Export scale 2|3|4 (default 3)
  --dark            Export dark theme (default light)
  --timeout <ms>    Page wait timeout (default 60000)
  --help            Show this help
`);
}

function parseArgs(argv) {
  const args = {
    html: "",
    md: "",
    out: "",
    title: "",
    hint: "",
    basename: "",
    scale: 3,
    dark: false,
    timeout: 60000,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const next = argv[i + 1];
    if (a === "--help" || a === "-h") {
      args.help = true;
    } else if (a === "--html" && next) {
      args.html = next;
      i++;
    } else if (a === "--md" && next) {
      args.md = next;
      i++;
    } else if (a === "--out" && next) {
      args.out = next;
      i++;
    } else if (a === "--title" && next) {
      args.title = next;
      i++;
    } else if (a === "--hint" && next) {
      args.hint = next;
      i++;
    } else if (a === "--basename" && next) {
      args.basename = next;
      i++;
    } else if (a === "--scale" && next) {
      args.scale = Number(next);
      i++;
    } else if (a === "--timeout" && next) {
      args.timeout = Number(next);
      i++;
    } else if (a === "--dark") {
      args.dark = true;
    } else {
      throw new Error(`Unknown or incomplete argument: ${a}`);
    }
  }
  return args;
}

function extractMermaid(md) {
  const match = md.match(/```mermaid\r?\n([\s\S]*?)```/);
  if (!match) {
    throw new Error("No ```mermaid fenced block found in Markdown");
  }
  return match[1];
}

function chromeCandidates() {
  if (process.env.CHROME_PATH) return [process.env.CHROME_PATH];
  if (process.platform === "darwin") {
    return [
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Chromium.app/Contents/MacOS/Chromium",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ];
  }
  if (process.platform === "win32") {
    const pf = process.env.PROGRAMFILES || "C:\\Program Files";
    const pf86 = process.env["PROGRAMFILES(X86)"] || "C:\\Program Files (x86)";
    const local = process.env.LOCALAPPDATA || "";
    return [
      join(pf, "Google", "Chrome", "Application", "chrome.exe"),
      join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
      join(local, "Google", "Chrome", "Application", "chrome.exe"),
      join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
    ];
  }
  return [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/snap/bin/chromium",
  ];
}

function resolveChrome() {
  for (const p of chromeCandidates()) {
    if (p && existsSync(p)) return p;
  }
  return "";
}

async function resolvePlaywright() {
  if (process.env.PLAYWRIGHT_CORE && existsSync(process.env.PLAYWRIGHT_CORE)) {
    return import(pathToFileURL(process.env.PLAYWRIGHT_CORE).href);
  }

  // Prefer the skill's declared runtime dependency, then allow a project-local package.
  for (const packageRoot of [skillRoot, process.cwd()]) {
    const require = createRequire(join(packageRoot, "package.json"));
    for (const id of ["playwright-core", "playwright", "@playwright/test"]) {
      try {
        const pkgJson = require.resolve(`${id}/package.json`);
        const root = dirname(pkgJson);
        for (const entry of ["index.mjs", "index.js"]) {
          const full = join(root, entry);
          if (existsSync(full)) {
            return import(pathToFileURL(full).href);
          }
        }
      } catch {
        // try next
      }
    }
  }

  // pnpm nested layout under cwd
  const pnpmRoot = join(process.cwd(), "node_modules", ".pnpm");
  if (existsSync(pnpmRoot)) {
    const { readdirSync } = await import("node:fs");
    const entries = readdirSync(pnpmRoot).filter((n) => n.startsWith("playwright-core@"));
    for (const entry of entries) {
      const full = join(pnpmRoot, entry, "node_modules", "playwright-core", "index.mjs");
      if (existsSync(full)) {
        return import(pathToFileURL(full).href);
      }
    }
  }

  throw new Error(
    "Cannot find playwright-core/playwright. Run npm install --omit=dev --prefix <skill-dir>, install a project dependency, or set PLAYWRIGHT_CORE to index.mjs",
  );
}

function contentType(filePath) {
  switch (extname(filePath).toLowerCase()) {
    case ".html":
      return "text/html; charset=utf-8";
    case ".md":
      return "text/markdown; charset=utf-8";
    case ".js":
    case ".mjs":
      return "text/javascript; charset=utf-8";
    case ".css":
      return "text/css; charset=utf-8";
    case ".svg":
      return "image/svg+xml";
    case ".png":
      return "image/png";
    default:
      return "application/octet-stream";
  }
}

async function buildTempHtmlFromMd(args) {
  const mdPath = resolve(args.md);
  const md = await readFile(mdPath, "utf8");
  const mermaid = extractMermaid(md);
  const template = await readFile(defaultTemplate, "utf8");
  const title = args.title || basename(mdPath, ".md");
  const base = args.basename || basename(args.out, ".png") || "business-flow";
  const escaped = mermaid.replace(/<\/script>/gi, "<\\/script>");

  let html = template
    .replace(/<title>.*?<\/title>/, `<title>${title} · 预览与导出</title>`)
    .replace(/<b id="title">.*?<\/b>/, `<b id="title">${title}</b>`);

  if (args.hint) {
    html = html.replace(
      /<div id="hint">[\s\S]*?<\/div>/,
      `<div id="hint">${args.hint}</div>`,
    );
  }

  html = html.replace(
    /<script type="text\/plain" id="fallback-source">[\s\S]*?<\/script>/,
    `<script type="text/plain" id="fallback-source">\n${escaped}\n</script>`,
  );

  // Force basename for downloads inside the temp page.
  html = html.replace(
    'const basename = params.get("basename") || "business-flow";',
    `const basename = params.get("basename") || ${JSON.stringify(base)};`,
  );

  const dir = await mkdtemp(join(tmpdir(), "rumo-mermaid-"));
  const htmlPath = join(dir, "preview.html");
  await writeFile(htmlPath, html, "utf8");
  // Optional: also place md beside html for fetch parity
  await writeFile(join(dir, basename(mdPath)), md, "utf8");
  return { htmlPath, cleanupDir: dir };
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    printHelp();
    process.exit(0);
  }
  if (!args.out) {
    printHelp();
    throw new Error("--out is required");
  }
  if (!args.html && !args.md) {
    printHelp();
    throw new Error("Provide --html or --md");
  }
  if (![2, 3, 4].includes(args.scale)) {
    throw new Error("--scale must be 2, 3, or 4");
  }

  let htmlPath = args.html ? resolve(args.html) : "";
  let serveRoot = "";
  let cleanupDir = "";

  if (args.md) {
    const built = await buildTempHtmlFromMd(args);
    htmlPath = built.htmlPath;
    serveRoot = dirname(htmlPath);
    cleanupDir = built.cleanupDir;
  } else {
    serveRoot = dirname(htmlPath);
  }

  const outPath = resolve(args.out);
  const chromePath = resolveChrome();
  const playwrightMod = await resolvePlaywright();
  const { chromium } = playwrightMod;

  const server = createServer(async (req, res) => {
    try {
      const urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
      let filePath = join(serveRoot, urlPath === "/" ? basename(htmlPath) : urlPath.replace(/^\//, ""));
      // Also allow absolute-ish sibling reads when exporting project HTML that fetches ./foo.md
      if (!filePath.startsWith(serveRoot)) {
        res.writeHead(403);
        res.end("forbidden");
        return;
      }
      if (!existsSync(filePath) && args.html) {
        // When project HTML fetches a relative md next to it, serveRoot already covers it.
      }
      const data = await readFile(filePath);
      res.writeHead(200, { "Content-Type": contentType(filePath) });
      res.end(data);
    } catch (err) {
      res.writeHead(404);
      res.end(String(err));
    }
  });

  await new Promise((resolveListen) => server.listen(0, "127.0.0.1", resolveListen));
  const { port } = server.address();

  const launchOpts = { headless: true };
  if (chromePath) {
    launchOpts.executablePath = chromePath;
  }

  let browser;
  try {
    browser = await chromium.launch(launchOpts);
  } catch (err) {
    server.close();
    throw new Error(
      `Failed to launch browser (chrome=${chromePath || "playwright-default"}): ${err.message}`,
    );
  }

  try {
    const page = await browser.newPage({
      viewport: { width: 1800, height: 1400 },
      deviceScaleFactor: 2,
    });

    const query = new URLSearchParams();
    query.set("scale", String(args.scale));
    if (args.title) query.set("title", args.title);
    if (args.hint) query.set("hint", args.hint);
    if (args.basename) query.set("basename", args.basename);
    if (args.md) {
      // temp page uses fallback only; no md fetch required
    } else if (args.html) {
      // keep relative md fetch working for project pages
    }

    const pageUrl = `http://127.0.0.1:${port}/${basename(htmlPath)}?${query.toString()}`;
    const downloadPromise = page.waitForEvent("download", { timeout: args.timeout });
    await page.goto(pageUrl, { waitUntil: "networkidle", timeout: args.timeout });
    await page.waitForSelector("#stage svg", { timeout: args.timeout });
    await page.waitForTimeout(1500);

    if (args.dark) {
      // Click theme toggle if currently light (default dark=false in template).
      const isDark = await page.evaluate(() => document.documentElement.classList.contains("dark"));
      if (!isDark) {
        await page.click("#theme");
        await page.waitForTimeout(800);
        await page.waitForSelector("#stage svg", { timeout: args.timeout });
      }
    }

    await page.selectOption("#scale", String(args.scale));
    await page.click("#png");
    const download = await downloadPromise;
    await download.saveAs(outPath);
    console.log(`saved ${outPath}`);
  } finally {
    await browser.close();
    server.close();
    if (cleanupDir) {
      await rm(cleanupDir, { recursive: true, force: true });
    }
  }
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
