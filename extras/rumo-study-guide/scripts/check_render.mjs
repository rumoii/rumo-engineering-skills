#!/usr/bin/env node
// Check a local guide using an existing Playwright installation; never download a browser.
import { mkdir, stat } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { isAbsolute, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

function parseArgs(args) {
  let guide;
  let out;
  for (let index = 0; index < args.length; index++) {
    const arg = args[index];
    if (arg === '--out' && !out && args[index + 1] && !args[index + 1].startsWith('--')) {
      out = resolve(args[++index]);
    } else if (!arg.startsWith('-') && !guide) {
      guide = resolve(arg);
    } else {
      throw new Error('Usage: node check_render.mjs <guide.html> [--out <dir>]');
    }
  }
  if (!guide) throw new Error('Usage: node check_render.mjs <guide.html> [--out <dir>]');
  return { guide, out };
}

async function loadPlaywright() {
  if (process.env.PLAYWRIGHT_MODULE) {
    const directory = process.env.PLAYWRIGHT_MODULE;
    if (!isAbsolute(directory) || !(await stat(directory)).isDirectory()) {
      throw new Error('PLAYWRIGHT_MODULE must be an absolute path to a Playwright module directory');
    }
    const entry = createRequire(import.meta.url).resolve(directory);
    return import(pathToFileURL(entry).href);
  }
  return import('playwright');
}

const allowed = url => ['file:', 'data:', 'about:'].includes(new URL(url).protocol);

async function checkCombination(browser, url, viewport, colorScheme, out) {
  const result = { viewport, colorScheme, overflow: null, issues: [] };
  let context;
  try {
    context = await browser.newContext({ viewport, offline: true, serviceWorkers: 'block' });
    await context.route('**/*', route => allowed(route.request().url()) ? route.continue() : route.abort());
    const page = await context.newPage();
    page.setDefaultTimeout(15_000);
    const external = new Set();
    const recordRequest = requestUrl => {
      if (!allowed(requestUrl) && !external.has(requestUrl)) {
        external.add(requestUrl);
        result.issues.push({ type: 'network-request', url: requestUrl });
      }
    };
    context.on('request', request => recordRequest(request.url()));
    page.on('websocket', socket => recordRequest(socket.url()));
    page.on('pageerror', error => result.issues.push({ type: 'pageerror', message: error.message }));
    page.on('console', message => {
      if (message.type() === 'error') result.issues.push({ type: 'console-error', message: message.text() });
    });
    await page.emulateMedia({ colorScheme });
    await page.goto(url, { waitUntil: 'load' });
    await page.evaluate(async () => {
      await document.fonts.ready;
      await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)));
    });
    const dom = await page.evaluate(() => {
      const ids = new Set();
      const duplicates = new Set();
      for (const element of document.querySelectorAll('[id]')) {
        if (ids.has(element.id)) duplicates.add(element.id);
        ids.add(element.id);
      }
      const missing = [];
      for (const anchor of document.querySelectorAll('a[href^="#"]')) {
        const href = anchor.getAttribute('href');
        if (href === '#') continue;
        let id;
        try { id = decodeURIComponent(href.slice(1)); }
        catch { missing.push(href); continue; }
        if (!document.getElementById(id)) missing.push(href);
      }
      return {
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        duplicates: [...duplicates], missing,
      };
    });
    result.overflow = dom.overflow;
    if (dom.overflow > 0) result.issues.push({ type: 'horizontal-overflow', pixels: dom.overflow });
    for (const id of dom.duplicates) result.issues.push({ type: 'duplicate-id', id });
    for (const href of dom.missing) result.issues.push({ type: 'missing-anchor', href });
    if (out) {
      result.screenshot = join(out, `${viewport.width}-${viewport.height}-${colorScheme}.png`);
      await page.screenshot({ path: result.screenshot, fullPage: true, timeout: 15_000 });
    }
  } catch (error) {
    result.issues.push({ type: 'render-error', message: error.message });
  } finally {
    if (context) {
      try { await context.close(); }
      catch (error) { result.issues.push({ type: 'cleanup-error', message: error.message }); }
    }
  }
  return result;
}

async function main() {
  const results = { combinations: [], issues: [] };
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
    if (!(await stat(options.guide)).isFile()) throw new Error('guide is not a file');
  } catch (error) {
    results.issues.push({ type: 'input-error', message: error.message });
    console.log(JSON.stringify(results, null, 2));
    console.log('FAIL');
    return 1;
  }

  let chromium;
  try {
    const playwright = await loadPlaywright();
    chromium = playwright.chromium ?? playwright.default?.chromium;
    if (!chromium) throw new Error('module does not export chromium');
  } catch (error) {
    console.error(`Playwright is unavailable: ${error.message}. Set PLAYWRIGHT_MODULE to an existing absolute module directory, or make playwright resolvable by Node. No dependency or browser was installed.`);
    return 2;
  }

  let browser;
  try {
    if (options.out) {
      await mkdir(options.out, { recursive: true });
      // Keep Chromium's possible debug.log beside the requested evidence.
      process.chdir(options.out);
    }
    results.url = pathToFileURL(options.guide).href;
    browser = await chromium.launch({ headless: true, timeout: 30_000 });
    for (const viewport of [{ width: 1366, height: 900 }, { width: 390, height: 844 }]) {
      for (const colorScheme of ['light', 'dark']) {
        results.combinations.push(await checkCombination(browser, results.url, viewport, colorScheme, options.out));
      }
    }
  } catch (error) {
    results.issues.push({ type: 'browser-error', message: error.message });
  } finally {
    if (browser) {
      try { await browser.close(); }
      catch (error) { results.issues.push({ type: 'cleanup-error', message: error.message }); }
    }
  }
  const failed = results.issues.length > 0 || results.combinations.some(result => result.issues.length > 0);
  console.log(JSON.stringify(results, null, 2));
  console.log(failed ? 'FAIL' : 'PASS');
  return failed ? 1 : 0;
}

process.exitCode = await main();
