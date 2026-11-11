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

async function checkInteraction(browser, url, options, check, initialize) {
  const result = { status: 'pass', issues: [] };
  let context;
  try {
    context = await browser.newContext({ offline: true, serviceWorkers: 'block', ...options });
    await context.route('**/*', route => allowed(route.request().url()) ? route.continue() : route.abort());
    context.on('request', request => {
      if (!allowed(request.url())) result.issues.push({ type: 'network-request', url: request.url() });
    });
    if (initialize) await context.addInitScript(initialize);
    const page = await context.newPage();
    page.setDefaultTimeout(5_000);
    page.on('pageerror', error => result.issues.push({ type: 'pageerror', message: error.message }));
    page.on('console', message => {
      if (message.type() === 'error') result.issues.push({ type: 'console-error', message: message.text() });
    });
    await page.goto(url, { waitUntil: 'load' });
    await check(page, result);
  } catch (error) {
    result.issues.push({ type: 'interaction-error', message: error.message });
  } finally {
    if (context) {
      try { await context.close(); }
      catch (error) { result.issues.push({ type: 'cleanup-error', message: error.message }); }
    }
  }
  if (result.issues.length) result.status = 'fail';
  return result;
}

async function printColors(page) {
  return page.evaluate(() => {
    // Relative sRGB luminance: exact white background; text no lighter than #555.
    function luminance(rgb) {
      return rgb.slice(0, 3).map(value => {
        const channel = value / 255;
        return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
      }).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
    }
    function rgba(color) {
      const channels = color.match(/[\d.]+/g)?.map(Number);
      if (!channels || channels.length < 3) throw new Error(`Unsupported computed color: ${color}`);
      return [...channels.slice(0, 3), channels[3] ?? 1];
    }
    function over(foreground, background) {
      return foreground.slice(0, 3).map((channel, index) =>
        channel * foreground[3] + background[index] * (1 - foreground[3]));
    }
    const thresholds = { background: luminance([255, 255, 255]), text: luminance([85, 85, 85]) };
    function inspect(element) {
      const ancestors = [];
      for (let node = element; node; node = node.parentElement) ancestors.unshift(node);
      let background = [255, 255, 255];
      for (const node of ancestors) background = over(rgba(getComputedStyle(node).backgroundColor), background);
      const style = getComputedStyle(element);
      const text = over(rgba(style.color), background);
      const backgroundLuminance = luminance(background);
      const textLuminance = luminance(text);
      return {
        background: style.backgroundColor, color: style.color,
        effectiveBackground: background, backgroundLuminance, textLuminance,
        pass: backgroundLuminance >= thresholds.background - 1e-6 && textLuminance <= thresholds.text,
      };
    }
    const answer = document.querySelector('details.answer');
    return { thresholds, body: inspect(document.body), answer: answer ? inspect(answer) : null };
  });
}

async function checkInteractions(browser, url) {
  const checks = {};
  checks.initialization = await checkInteraction(browser, url, {}, async (page, result) => {
    result.initialized = await page.locator('html').evaluate(el => el.classList.contains('js'));
    result.answerCount = await page.locator('details.answer').count();
    if (!result.initialized) result.issues.push({ type: 'script-not-initialized' });
  });
  checks.expandedDetails = await checkInteraction(browser, url,
    { viewport: { width: 390, height: 844 } }, async (page, result) => {
      const expanded = await page.evaluate(async () => {
        const details = [...document.querySelectorAll('details')];
        details.forEach(el => { el.open = true; });
        await document.fonts.ready;
        await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)));
        return { count: details.length, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth };
      });
      Object.assign(result, expanded);
      if (result.overflow > 0) result.issues.push({ type: 'expanded-horizontal-overflow', pixels: result.overflow });
    });
  checks.noJavaScript = await checkInteraction(browser, url, { javaScriptEnabled: false }, async (page, result) => {
    const content = await page.evaluate(() => {
      const answers = [...document.querySelectorAll('details.answer')].map(el => {
        const clone = el.cloneNode(true);
        clone.querySelectorAll('summary,script,style').forEach(node => node.remove());
        return clone.textContent.trim().length;
      });
      const main = document.querySelector('main') ?? document.body;
      const clone = main.cloneNode(true);
      clone.querySelectorAll('script,style,nav,.toolbar,noscript,details.answer').forEach(node => node.remove());
      return { answerLengths: answers, bodyLength: clone.textContent.trim().length,
        bodyVisible: main.getBoundingClientRect().height > 0 };
    });
    Object.assign(result, content);
    if (content.answerLengths.some(length => length === 0) ||
        content.answerLengths.length !== checks.initialization.answerCount) {
      result.issues.push({ type: 'nojs-empty-answer' });
    }
    if (!content.bodyLength || !content.bodyVisible) result.issues.push({ type: 'nojs-empty-body' });
  });
  checks.blockedStorage = await checkInteraction(browser, url, {}, async (page, result) => {
    // Exercise a save as well as the initialization read.
    if (await page.locator('#theme').count()) await page.selectOption('#theme', 'dark');
    result.initialized = await page.locator('html').evaluate(el => el.classList.contains('js'));
    result.attempts = await page.evaluate(() => window.__storageAttempts);
    if (!result.initialized) result.issues.push({ type: 'script-not-initialized' });
  }, () => {
    window.__storageAttempts = { getItem: 0, setItem: 0 };
    for (const method of ['getItem', 'setItem']) {
      Object.defineProperty(Storage.prototype, method, { configurable: true, value() {
        window.__storageAttempts[method]++;
        throw new Error(`Storage.${method} blocked for acceptance`);
      } });
    }
  });
  for (const [name, colorScheme, theme] of [
    ['printManualDark', 'light', 'dark'], ['printSystemDark', 'dark', 'system'],
  ]) {
    checks[name] = await checkInteraction(browser, url, { colorScheme }, async (page, result) => {
      if (await page.locator('#theme').count()) await page.selectOption('#theme', theme);
      await page.emulateMedia({ media: 'print' });
      result.colors = await printColors(page);
      if (!result.colors.body.pass || result.colors.answer?.pass === false) {
        result.issues.push({ type: 'print-colors' });
      }
    });
  }
  checks.sourceLinks = await checkInteraction(browser, url, {}, async (page, result) => {
    const first = page.locator('a[data-abs]').first();
    if (!(await first.count())) {
      result.status = 'skipped';
      result.reason = 'No a[data-abs] references';
      return;
    }
    const select = page.getByRole('combobox', { name: '打开源码用' });
    await select.selectOption('cursor');
    result.href = await first.getAttribute('href');
    if (!result.href?.startsWith('cursor://file/')) result.issues.push({ type: 'source-cursor-href' });
    await page.reload({ waitUntil: 'load' });
    result.persistedChoice = await select.inputValue();
    result.persistedHref = await first.getAttribute('href');
    if (result.persistedChoice !== 'cursor' || !result.persistedHref?.startsWith('cursor://file/')) {
      result.issues.push({ type: 'source-choice-not-persisted' });
    }
  });
  return checks;
}

async function main() {
  const results = { combinations: [], interactions: {}, issues: [] };
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
    results.interactions = await checkInteractions(browser, results.url);
  } catch (error) {
    results.issues.push({ type: 'browser-error', message: error.message });
  } finally {
    if (browser) {
      try { await browser.close(); }
      catch (error) { results.issues.push({ type: 'cleanup-error', message: error.message }); }
    }
  }
  const failed = results.issues.length > 0 || results.combinations.some(result => result.issues.length > 0) ||
    Object.values(results.interactions).some(result => result.status === 'fail');
  console.log(JSON.stringify(results, null, 2));
  console.log(failed ? 'FAIL' : 'PASS');
  return failed ? 1 : 0;
}

process.exitCode = await main();
