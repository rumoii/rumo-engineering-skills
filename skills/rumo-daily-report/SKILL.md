---
name: rumo-daily-report
description: "Generate a plain-language Chinese daily report from the current completed conversation and append it to the configured date-based TXT file when the user asks to整理日报 or generate a daily report."
---

# Incremental daily report

Use this skill when the user asks to `整理日报`, `生成日报`, or explicitly invokes `$rumo-daily-report` after completing work in the current conversation.

## Purpose and boundaries

- Produce a personal, cross-project engineering daily report that a manager or non-specialist can understand at a glance.
- Read only the current conversation and clearly related evidence already collected in it. Historical report files provide continuity, numbering, and style; they do not provide facts for the current batch.
- Append only the current conversation's new work to the local report for the machine's current local date. Do not rewrite, reorder, or silently merge existing entries.
- Do not claim a fix, cause, percentage, deployment, or other result that the conversation does not establish.
- This skill writes the daily TXT because the user explicitly requested incremental local accumulation. It is separate from `engineering-task-summary`, which handles structured engineering archives when the user asks to summarize and save an engineering task.

## First-use and file selection

1. If no fixed report directory is configured, ask the user for the directory once. Do not guess a product path. Configure it with the bundled script and reuse it thereafter.
2. Use the local date at execution time and the exact filename `YYYY-MM-DD-日报.txt`, for example `2026-08-27-日报.txt`.
3. Keep configuration and deduplication state under the user's Codex configuration directory, not in the report directory. Never put credentials or tokens in either location.

## Extract and write

1. Extract only work completed or materially advanced in this conversation. Separate unrelated problems and preserve system or product ownership when it is needed for comprehension.
2. Write each top-level item in one of these structures:

   ```text
   1.解决了XX问题，原因是XX，解决方案是XX。
   2.推进了XX的开发/工作，进度大约从XX%推进到XX%，主要汇报以下几点：
   ①……
   ②……
   3.解决了XX问题，原因是XX，解决方案是XX。
   ```

3. Use the user's preferred verbs and concise formal Chinese. Put the business result first, explain the cause in plain language, then state the solution. Keep necessary technical names after their plain-language explanation.
4. Use a progress percentage only when the current conversation provides it or the user confirms it. Otherwise use an actual milestone such as “目前已完成……”.
5. Do not add a mandatory verification-status sentence. If work is incomplete, reflect that truth through wording such as “推进了”“完成了原因分析” or “正在处理”; never turn an analysis or code change into “解决了”.
6. If the user says “不要修改内容” or “只排列顺序”, preserve supplied wording and only perform the requested numbering, ordering, merging, or splitting. If the user requests an oral version, shorten it without dropping the subject, key cause, solution, or actual state.
7. Pass unnumbered item text to `scripts/daily_report.py append`. The script assigns the next continuous numbers for that date and skips exact normalized duplicates. Use the current conversation/thread identifier as `--session-id` when available.
8. After a successful append, report the added text, date file path, and number range. If there is no new factual work, do not write a placeholder; tell the user that nothing new was appended.

## Failure handling

- Stop without replacing the existing report when the configured directory is missing, the report is not valid UTF-8, numbering cannot be determined, the state is corrupt, or the file cannot be locked or atomically replaced.
- Report the concrete failure and preserve the original file. Do not create a second fallback report in another directory.

## Bundled script

Resolve the script relative to this skill directory. Configure the directory once:

```powershell
py -3 scripts\daily_report.py configure --report-dir "D:\path\to\daily-reports"
```

Only when the user explicitly asks to change the fixed directory, run the same command with `--replace`.

Append JSON-encoded unnumbered items for the current batch:

```powershell
py -3 scripts\daily_report.py append --session-id "<current-thread-id>" --items-json '["解决了……，原因是……，解决方案是……。"]'
```

Use `--date YYYY-MM-DD` only for deterministic tests or an explicitly requested date; normal use derives the machine's local date.
