# Learning Components

Read this when selecting markup. The fragments show structure only; their class
names are suggestions, and each guide styles them in its own design. Keep the
hooks under Script Hooks, keep ids unique, and update every return link after
renaming a section. Use the component criteria in
[writing.md](writing.md); not every component belongs in every chapter.

## Script Hooks

The template script and `check_render.mjs` rely on these; keep them in any design:

- `html.js` added at the end of initialization; elements with `js-only` stay hidden without it.
- Toolbar controls `#theme` (system/light/dark), `#present`, and `#source-opener`
  labeled “打开源码用”, plus an empty `#storage-status` for storage failures.
- Guarded `localStorage` reads and writes under a storage key unique to the guide.
- Answers in native `details.answer` elements whose text is in the HTML.
- A print rule that sets white paper and dark text for `:root`, `:root[data-theme]`,
  and `:root:not([data-theme="light"])`, so manual and system dark themes print light.
  Theme rules added later win over an earlier print rule of equal specificity, so
  a design that adds its own color variables restates every one of them in a print
  rule after its theme rules.
- `a[data-abs]` source links rewritten by the opener selector.

## Chapter Opening

Open with why the reader should care and a goal the reader can attempt. For a
dated sprint, put the priority and estimated time in the kicker line, defined
for this reader; estimates are planning judgments, not measured learning speed.

```html
<header>
  <p class="kicker">第 2 章　P0　约 15 分钟</p>
  <h1>多加一个数，总数会怎么变</h1>
  <p class="lead">购物车算总价、统计访问量，都在做同一件事：……</p>
  <div class="goal"><b>读完你能</b>不看代码，说出从 1 加到 4 每一步的总数。</div>
</header>
```

## Term Note And Key Sentence

Explain a term where it first appears, in the paragraph or in a note placed
beside it; on narrow screens the note sits inline before the paragraph. Mark at
most one key sentence per section.

```html
<aside class="note"><b>累加器</b>：装“到目前为止的总数”的变量，比如 total。</aside>
<p>……程序里装这个总数的变量叫<span class="term">累加器</span>。</p>
<p><span class="key">罐子里原来的钱从来不倒掉，每次只是往里再放一点。</span></p>
```

## Figure

Draw the mechanism as inline SVG: boxes for the parts, arrows for what passes
between them, labels in the reader's words. Give it a `title` for screen
readers, take colors from the page's CSS variables so both themes stay legible,
and put it beside the paragraph it explains. When labels would shrink below
reading size on a narrow screen, let the figure scroll inside its own box
rather than the page.

```html
<figure>
  <svg viewBox="0 0 520 300" role="img" aria-labelledby="pipe-title">
    <title id="pipe-title">agent 把要求交给派活脚本，脚本读 adapter 后启动 Codex</title>
    <!-- boxes, arrows, and labels for this mechanism -->
  </svg>
  <figcaption>一句话说明这张图要读者看出什么。</figcaption>
</figure>
```

## Code Walkthrough

Pair a short real excerpt with a plain-language translation, line by line.
Say once, in plain words, when code was written for teaching rather than taken
from the project. The pair stacks vertically on narrow screens.

```html
<div class="xlate">
  <div class="h">代码</div><div class="h">白话</div>
  <div class="o">total = 0</div><div>罐子先是空的。</div>
  <div class="o">    total += value</div><div>把当天的钱放进罐子，原来的钱还在。</div>
</div>
```

## Self-Test And Similar Task

Ask for an independent answer, then give the reasoning, the usual mistake, and
a return link. Put a few in every chapter, not only at the end. After a worked
example, ask the same task with one changed input. Revealing an answer is not
passing a test.

```html
<section class="practice" id="practice">
  <h2>自己试试</h2>
  <div class="q">
    <p>1. 从 1 加到 6 是多少？比从 1 加到 5 多多少？</p>
    <details class="answer"><summary>看答案</summary>
      <p>21，比 15 多 6。前五天的钱都在，只多了第六天的 6 块。<a href="#jar">回看存钱罐</a></p>
    </details>
  </div>
</section>
```

## Prediction Before Reveal

Use when changing one condition reveals a mechanism. Ask for a reason; do not
force input or block further reading.

```html
<p>如果放 5 天而不是 4 天，罐子里会多出多少？先想好理由再点开。</p>
<details class="answer"><summary>看答案</summary>
  <p>多 5 块。前 4 天的 10 块都还在，第 5 天再放进 5 块。<a href="#jar">回看存钱罐</a></p>
</details>
```

## Parameter Experiment

Keep the formula and the initial worked value in static HTML; only the control
needs JavaScript. This fragment uses the template's sum handler; replace both
the calculation and the explanation for a different mechanism, and do not paste
a second copy with the same ids.

```html
<div class="lab">
  <h3>自己调一调</h3><p>先猜一个数，再拖动滑块看结果。</p>
  <details class="answer"><summary>打开滑块</summary>
    <div class="range-row js-only">
      <label for="sum-n">放几天</label><output id="sum-n-value" for="sum-n">4</output>
      <input id="sum-n" type="range" min="1" max="20" step="1" value="4">
    </div>
    <p>用现成的公式算：<output id="sum-formula">4 × (4 + 1) ÷ 2</output> =
      <output class="model-number" id="sum-result" aria-live="polite">10</output>。</p>
  </details>
</div>
```

## Open Retelling

Use for synthesis or interview preparation: ask the reader to explain the whole
path aloud, then give the points a good answer covers. Different wording is fine.
Use the self-test markup with a summary such as “看参考讲法”.

## Review List And Local Self-Reports

Ask the reader to retry a core task in a later session. Use unique `data-review`
values and radio group names; the template stores `yes` / `no` in localStorage.
If storage fails, the lesson and current controls still work. A self-report is
the reader's own judgment, not evidence of mastery.

```html
<section class="review" id="review" aria-labelledby="review-title">
  <h2 id="review-title">下次打开，先做这题</h2>
  <article class="review-card" data-review="g2">
    <p>放的天数从 6 变成 7，总数怎么变？</p>
    <fieldset class="mark js-only"><legend>这题我</legend>
      <label><input type="radio" name="review-g2" value="yes"> 会</label>
      <label><input type="radio" name="review-g2" value="no"> 还不会</label>
    </fieldset>
    <details class="answer"><summary>看答案</summary>
      <p>多出第 7 天的 7 块，从 21 变成 28。<a href="#jar">回看存钱罐</a></p>
    </details>
  </article>
</section>
```

## Source Link

Put a small “看原文” link after the sentence or code it supports, only where a
reader may want to open the source. Do not collect links into an index at the
end; the evidence record belongs in `report.md`. Replace the example path, line,
and substring with checked evidence; all three attributes must be on the same
anchor. The template's live example uses a placeholder path; replace it before
delivering a guide.

```html
<a class="src" href="vscode://file//path/to/repo/src/example.py:3" data-p="src/example.py" data-l="3" data-s="total">看原文</a>
<a class="src" href="vscode://file//path/to/repo/lib/helpers.py:8" data-p="LIB:helpers.py" data-l="8" data-s="def combine">看原文</a>
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
is unavailable, without installing anything. With `--out <dir>` it also saves
a full-page screenshot for each width and theme; look at them before delivery.
Answer correctness, plain language, and figure/text agreement still need a
reader: see the cold read in SKILL.md. These checks do not establish learning.
