#!/usr/bin/env node
// Exercise the real checker against disposable HTML fixtures; never install a browser.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, isAbsolute, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import test from 'node:test';

const here = dirname(fileURLToPath(import.meta.url));
const checker = join(here, 'check_render.mjs');
let unavailable;
let browser;
let chromium;
try {
  const directory = process.env.PLAYWRIGHT_MODULE;
  if (directory && !isAbsolute(directory)) throw new Error('PLAYWRIGHT_MODULE must be absolute');
  const module = directory
    ? await import(pathToFileURL(createRequire(import.meta.url).resolve(directory)).href)
    : await import('playwright');
  chromium = module.chromium ?? module.default?.chromium;
  browser = await chromium.launch({ headless: true });
} catch (error) {
  unavailable = `Existing Playwright/Chromium unavailable: ${error.message}; no installation attempted`;
} finally {
  if (browser) await browser.close();
}

test('render acceptance fixtures', { skip: unavailable, timeout: 240_000 }, async t => {
  const template = await readFile(join(here, '../assets/template.html'), 'utf8');
  const parent = await realpath(tmpdir());
  const directory = await mkdtemp(join(parent, 'study-guide-render-'));
  // Only remove this suite's newly created directory inside the resolved system TEMP.
  t.after(async () => {
    assert.equal(dirname(await realpath(directory)), parent);
    await rm(directory, { recursive: true, force: true });
  });

  async function check(name, html) {
    const fixture = join(directory, `${name}.html`);
    await writeFile(fixture, html);
    const run = spawnSync(process.execPath, [checker, fixture], {
      encoding: 'utf8', timeout: 60_000, cwd: directory,
    });
    assert.ifError(run.error);
    assert.ok([0, 1].includes(run.status), run.stderr || run.stdout);
    const output = run.stdout.trimEnd();
    const split = output.lastIndexOf('\n');
    assert.ok(split >= 0, run.stdout);
    return { status: run.status, result: JSON.parse(output.slice(0, split)), marker: output.slice(split + 1) };
  }

  async function negative(name, html, checkName, issueType) {
    const run = await check(name, html);
    assert.equal(run.status, 1, `${name} incorrectly passed`);
    assert.equal(run.marker, 'FAIL');
    const result = run.result.interactions?.[checkName];
    assert.equal(result?.status, 'fail', JSON.stringify(run.result));
    assert.ok(result.issues.some(issue => issue.type === issueType), JSON.stringify(result));
    t.diagnostic(`${name}: FAIL ${checkName} (${result.issues.map(issue => issue.type).join(', ')})`);
  }

  await t.test('normal template passes every interaction', async () => {
    const run = await check('normal', template);
    assert.equal(run.status, 0, JSON.stringify(run.result));
    assert.equal(run.marker, 'PASS');
    for (const result of Object.values(run.result.interactions ?? {})) assert.equal(result.status, 'pass');
    assert.equal(run.result.interactions?.sourceLinks?.status, 'pass');
  });

  await t.test('removing the optional sum input still passes', async () => {
    const stripped = template.replace(/<input[^>]*id="sum-n"[^>]*>/, '');
    assert.notEqual(stripped, template);
    const run = await check('no-sum', stripped);
    assert.equal(run.status, 0, JSON.stringify(run.result));
  });

  await t.test('old no-sum initialization defect fails', async () => {
    const broken = template.replace(/<input[^>]*id="sum-n"[^>]*>/, '')
      .replace("one('#sum-n')?.addEventListener", "one('#sum-n').addEventListener");
    assert.notEqual(broken, template);
    await negative('old-no-sum', broken, 'initialization', 'script-not-initialized');
  });

  await t.test('old root-only dark print rule fails in both dark modes', async () => {
    const broken = template.replace(':root,:root[data-theme],:root:not([data-theme="light"]){--bg:#fff', ':root{--bg:#fff');
    assert.notEqual(broken, template);
    const run = await check('dark-print', broken);
    assert.equal(run.status, 1);
    for (const key of ['printManualDark', 'printSystemDark']) {
      assert.equal(run.result.interactions?.[key]?.status, 'fail', JSON.stringify(run.result));
      assert.ok(run.result.interactions[key].issues.some(issue => issue.type === 'print-colors'));
      t.diagnostic(`dark-print: FAIL ${key} (print-colors)`);
    }
  });

  await t.test('overflow revealed by opening details fails', async () => {
    const broken = template.replace('</main>', '<details><summary>wide answer</summary><div style="width:3000px">wide</div></details></main>');
    await negative('expanded-overflow', broken, 'expandedDetails', 'expanded-horizontal-overflow');
  });

  await t.test('transparent print answers over white paper pass', async () => {
    const html = template.replace('</style>', '@media print{details.answer{background:transparent!important}}</style>');
    const run = await check('transparent-print', html);
    assert.equal(run.status, 0, JSON.stringify(run.result));
    assert.equal(run.result.interactions.printManualDark.colors.answer.background, 'rgba(0, 0, 0, 0)');
  });

  await t.test('light print text on white paper fails', async () => {
    const html = template.replace('</style>', '@media print{body{color:#fff!important}}</style>');
    await negative('light-print-text', html, 'printManualDark', 'print-colors');
  });

  await t.test('answers generated only by JavaScript fail', async () => {
    const broken = template.replace(/(<details class="answer">)([\s\S]*?)(<\/details>)/, (_, start, body, end) => {
      const summary = body.match(/<summary>[\s\S]*?<\/summary>/)[0];
      return `${start}${summary}<div id="dynamic-answer"></div>${end}`;
    }).replace('</body>', '<script>document.getElementById("dynamic-answer").textContent = "answer only with JS";</script></body>');
    await negative('nojs-answer', broken, 'noJavaScript', 'nojs-empty-answer');
  });

  await t.test('unguarded storage read crashes initialization', async () => {
    const broken = template.replace("  let saved = {};", "  localStorage.getItem('unguarded');\n  let saved = {};");
    await negative('storage-read', broken, 'blockedStorage', 'pageerror');
  });

  await t.test('unguarded storage write crashes a control', async () => {
    const broken = template.replace('  function save() {', "  function save() {\n    localStorage.setItem('unguarded', 'value');");
    await negative('storage-write', broken, 'blockedStorage', 'pageerror');
  });

  await t.test('missing persistence of source choice fails', async () => {
    const broken = template.replace("state.source = event.target.value; apply(); save();", "state.source = event.target.value; apply();");
    assert.notEqual(broken, template);
    await negative('source-persistence', broken, 'sourceLinks', 'source-choice-not-persisted');
  });

  await t.test('pages without source links explicitly skip the switch check', async () => {
    const run = await check('no-source-links', template.replace(/ data-abs="[^"]*"/g, ''));
    assert.equal(run.status, 0, JSON.stringify(run.result));
    assert.equal(run.result.interactions?.sourceLinks?.status, 'skipped');
    assert.match(run.result.interactions.sourceLinks.reason, /a\[data-abs\]/);
  });

  await t.test('web targets and the no-JS default link are retained', async () => {
    const html = template.replace('data-abs="/path/to/repo/src/example.py"',
      'data-abs="/path/to/repo/src/example.py" data-web="https://example.org/blob/fixed/src/example.py#L3"');
    assert.notEqual(html, template);
    const run = await check('web-target', html);
    assert.equal(run.status, 0, JSON.stringify(run.result));
    const browser = await chromium.launch({ headless: true });
    try {
      const context = await browser.newContext({ offline: true });
      const page = await context.newPage();
      const url = pathToFileURL(join(directory, 'web-target.html')).href;
      await page.goto(url);
      const select = page.getByRole('combobox', { name: '打开源码用' });
      const first = page.locator('a[data-abs]').first();
      await select.selectOption('web');
      assert.equal(await first.getAttribute('href'), 'https://example.org/blob/fixed/src/example.py#L3');
      await page.reload();
      assert.equal(await select.inputValue(), 'web');
      await select.selectOption('vscode');
      assert.equal(await first.getAttribute('href'), 'vscode://file//path/to/repo/src/example.py:3');
      await page.goto(pathToFileURL(join(directory, 'normal.html')).href);
      assert.equal(await select.locator('option[value="web"]').count(), 0);
      const nojs = await browser.newContext({ offline: true, javaScriptEnabled: false });
      const staticPage = await nojs.newPage();
      await staticPage.goto(url);
      assert.equal(await staticPage.locator('a[data-abs]').first().getAttribute('href'),
        'vscode://file//path/to/repo/src/example.py:3');
      await nojs.close();
      await context.close();
    } finally {
      await browser.close();
    }
  });
});
