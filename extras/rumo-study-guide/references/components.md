# Learning Components

Read this when selecting markup. Copy the single-file template, then replace
its content. These fragments use its classes; keep ids unique and update every
review link after renaming a section. Use the optional-component criteria in
[writing.md](writing.md), not every component in every chapter.

## Chapter Self-Test And Similar Task

Ask for an independent answer, then offer reasoning and a precise return link.
Keep answers in native details so they work without JavaScript. Repeat this
structure in each chapter, not just once at the end of a long guide.

```html
<div class="quiz" data-component="quiz">
  <h3>分章自测 · G1</h3>
  <p>从 1 加到 6 的结果是多少？比加到 5 多多少？</p>
  <details class="answer">
    <summary>先自己答，再看答案与原因</summary>
    <p>结果是 21，多 6，因为只新增第六项。<a href="#principle">回看规则</a>。</p>
  </details>
</div>
```

After a complete worked example, use the same structure with `class="similar"`
and `data-component="similar"` for a changed-input problem. Do not count revealing
an answer as passing a test.

## Prediction Before Reveal

Use when changing one condition helps reveal a mechanism. Ask for a reason;
do not force an input or block further reading until the reader types something.

```html
<div class="prediction" data-component="predict">
  <h3>先预测再揭晓</h3>
  <p>终点从 4 改成 5，总数会增加多少？先说理由。</p>
  <details class="answer"><summary>说完预测，再揭晓</summary>
    <p>增加 5，因为新增一项 5。<a href="#principle">回看规则</a>。</p>
  </details>
</div>
```

## Parameter Experiment

Keep the formula, assumptions, and initial worked value in static HTML. Only
controls depend on JavaScript. This fragment uses the template's sum handler;
replace both the calculation and its explanation for a different mechanism.
The result stays folded until the reader chooses to reveal it.

```html
<div class="lab-model" data-component="lab">
  <h3>参数小实验：只改变终点</h3><p>先预测，再展开并调整 n。</p>
  <details class="answer"><summary>揭晓模型并调整参数</summary>
    <div class="range-row js-only">
      <label for="sum-n">终点 n</label><output id="sum-n-value" for="sum-n">4</output>
      <input id="sum-n" type="range" min="1" max="20" step="1" value="4">
    </div>
    <p>模型算式：<output id="sum-formula">4 × (4 + 1) ÷ 2</output> =
      <output class="model-number" id="sum-result" aria-live="polite">10</output></p>
    <p>教学模型，非实测。<a href="#example">回看逐步累加</a>。</p>
  </details>
</div>
```

Do not paste a second copy with the same ids. Extend the handler deliberately
if the guide needs multiple models; keep outputs and labels tied to that model.

## Code Walkthrough

Pair a short real excerpt with steps explaining what it does. Label invented
or unrun code. Source references belong next to repository excerpts; code names
alone do not prove a call path. The pair stacks vertically on narrow screens.

```html
<div class="walkthrough" data-component="walk">
  <h3>代码走读</h3><div class="walkpair">
    <figure class="excerpt"><pre><code>total += value</code></pre>
      <figcaption>教学片段，未运行。</figcaption></figure>
    <ol><li>读取此前的总数。</li><li>加上当前项并保存。</li></ol>
  </div>
</div>
```

## Review List And Local Self-Reports

Ask the reader to retry a core task in a later session. Use unique `data-review`
values and radio group names; the template stores `yes` / `no` in localStorage.
Keep its guarded reads and writes and choose a distinct storage key per guide
and content revision. If storage fails, the lesson and current controls still
work. Self-reports are the reader's judgment, not automatic mastery evidence.

```html
<section class="review" data-component="review" aria-labelledby="review-title">
  <h3 id="review-title">下次打开，合上正文再试</h3>
  <article class="review-card" data-review="g2">
    <p>n 从 6 到 7，总数怎样变化？</p>
    <fieldset class="mark js-only"><legend>我的自评</legend>
      <label><input type="radio" name="review-g2" value="yes"> 会</label>
      <label><input type="radio" name="review-g2" value="no"> 不会</label>
    </fieldset>
    <details class="answer"><summary>重答后查看解释</summary>
      <p>增加 7，从 21 到 28。<a href="#principle">回看规则</a>。</p>
    </details>
  </article>
</section>
```

## Priority And Time

Use for a dated sprint, defining what each priority demands from this reader.
Estimate time including practice; it is a plan, not a learning-speed measurement.

```html
<span class="badges" data-component="badges">
  <span class="badge">P0 能独立解释</span>
  <span class="badge time">预计 5 分钟</span>
</span>
```

## Open Retelling

Use for synthesis or spoken preparation. Give reference points and reasoning,
allow different wording, and keep evaluation with the reader.

```html
<div class="open" data-component="open"><h3>先自己讲一遍再看</h3>
  <p>解释 total 怎样保留此前的总数，并举一个变式。</p>
  <details class="answer"><summary>参考讲法与自评要点</summary>
    <p>先保留旧和，再加入当前项。检查是否说明这两点，并正确举例。
      <a href="#example">回看例子</a>。</p>
  </details>
</div>
```

## Term Hint

Use native details for mouse, touch, and keyboard access; no hover is required.
Explain central terms in the normal paragraph as well. Avoid hiding essential
definitions inside an optional component.

```html
<details class="term" data-component="terms"><summary>术语提示：累加器</summary>
  <div class="tooltip">保存中间总数的变量，如 total。</div>
</details>
```

## Source Annotation

Replace the example path, line, and substring with checked evidence. All three
attributes must occur on the same element. Visible text remains useful when
editor links are unavailable. The template's live example uses a clearly labeled
placeholder path; replace it before delivering a guide.

```html
<a class="ref" href="vscode://file//path/to/repo/src/example.py:3" data-p="src/example.py" data-l="3" data-s="total">src/example.py:3</a>
<a class="ref" href="vscode://file//path/to/repo/lib/helpers.py:8" data-p="LIB:helpers.py" data-l="8" data-s="def combine">LIB:helpers.py:8</a>
```

After building examples, run the linker from the installed skill directory:

```sh
python scripts/link_refs.py <guide.html> --root <dir> [--alias X=prefix/]...
```

It overwrites each `a[data-p]` href and adds a forward-slash `data-abs` path.
Other attributes and text stay unchanged; bytes outside those start tags stay
unchanged. Aliases follow the verifier's rules: `LIB:helpers.py` with
`--alias LIB=lib/` expands to `lib/helpers.py`; later definitions win.
Paths outside root, missing files, non-positive-integer lines, or `data-p` on
anything except an anchor exit 1 without writing the guide. Success prints
`ok: N links`. The linker does not check line contents; run the verifier next.

Two common href templates are `vscode://file/{abs}:{line}` (the default for
local code) and `https://host/owner/repo/blob/{commit}/{path}#L{line}` (web).
Available placeholders are `{abs}`, `{path}` (expanded relative path), `{line}`,
and `{commit}`; using `{commit}` requires `--commit` or exits 1 without writing.
Choose a fixed commit, not a moving branch. For readers without local code,
make the web URL the default href as well as the optional web target:

```sh
python scripts/link_refs.py <guide.html> --root <dir> --template "https://host/owner/repo/blob/{commit}/{path}#L{line}" --web-template "https://host/owner/repo/blob/{commit}/{path}#L{line}" --commit <sha>
```

For readers with local code, keep the default template and optionally supply
`--web-template` and `--commit` to add `data-web`. Ask if the reader's setup is
unknown. The toolbar's “打开源码用” selector rewrites `a[data-abs]` links to
VS Code or Cursor; “网页” appears only when at least one reference has `data-web`.
Web mode uses each available `data-web`; references without it retain their
current href. The initial choice follows a default web href when available,
otherwise VS Code; the saved choice takes precedence. Storage reads and writes
are guarded. Without JavaScript, the linker's default href remains clickable.
Only the VS Code and Cursor editor protocols are supported by the selector.

From the installed skill directory, run
`python scripts/verify_refs.py <guide.html> --root <dir> [--alias X=prefix/]... [--allow-empty]`.
For the second example, supply `--alias LIB=lib/` relative to the declared root.
The checker requires an existing file, an in-range line, and the expected text
on that line. Any failure exits 1. Zero references also exit 1 unless the
guide truly has no code references and you deliberately use `--allow-empty`.
This proves location only; manually verify meaning and surrounding conditions.

## Example Placeholders

Place these comments at block boundaries where a code/output block belongs,
not inside an existing pre or code element. Paths resolve against `--root`;
set it explicitly for reproducibility. The builder supplies escaped content.

```html
<!--CODE:examples/sum.py-->
<!--SNIPPET:examples/sum.py-->
<!--OUT:examples/sum.py-->
```

Run `python scripts/build_examples.py <template.html> --out <guide.html> [--root <dir>]`
from the installed skill directory. `CODE` embeds source; `SNIPPET` embeds source
with an unrun label; `OUT` runs the file and embeds actual output. Only `OUT`
executes. Python files use python, `.js` / `.mjs` use node, and `.java` uses java.
Each run has a 60-second timeout. Failure, timeout, or an unsupported executable
extension exits 1; never replace that failure with invented output. Inspect code
before running and observe the skill body's installation/external-service gate.

For final page checks, run `node scripts/check_render.mjs <guide.html> [--out <dir>]`.
It checks 1366/390 widths in both themes for overflow, page/console errors,
broken internal anchors, duplicate ids, and external requests. It also checks:

- The `html.js` initialization marker.
- All details expanded at 390 pixels without horizontal overflow.
- No-JavaScript body text and nonempty answers, with the same answer count.
- Initialization and a theme save while storage reads and writes throw.
- White print backgrounds and dark text on the body and first answer under
  manual and system dark themes. Transparent layers are composited over their
  ancestors and white paper; relative sRGB luminance must equal white for the
  background and be no greater than `#555` for text.
- Cursor source links and the selected value/href retained after reload.
  Pages without `a[data-abs]` explicitly report this check as skipped.

JSON reports each interaction separately. PASS/FAIL corresponds to exit 0/1;
missing Playwright exits 2. Normal Node
resolution or `PLAYWRIGHT_MODULE` locates Playwright; do not embed machine paths
in the guide. `node --test scripts/test_check_render.mjs` uses temporary fixtures
to check regressions; it explicitly skips when existing Playwright or Chromium
is unavailable, without installing anything. Manually check answer correctness,
explanation clarity, figure/text agreement, evidence links and self-report
persistence; these browser checks do not establish learning.
