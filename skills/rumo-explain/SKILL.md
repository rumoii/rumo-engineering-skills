---
name: rumo-explain
description: Use when the user asks how code in the current repository works, such as a function, subsystem, data flow, or feature, why it was built or changed that way, or wants it walked through before changing or reviewing it ("讲讲 X 是怎么工作的", "为什么这么设计", "这块代码在干什么"). Answer read-only from the code and its history, in plain words, smallest complete answer first. Do not use for general concept questions with no repository code, for a defect or unexpected behavior (use rumo-debug), for reviewing a diff (use rumo-review), or for resuming earlier work (use rumo-handoff).
---

# Rumo Explain

Give the user a working mental model of a piece of this repository: what it is, how it runs, and why it has this shape, each claim traceable to code or history.

## Authority

Explaining is read-only. Do not edit files, run commands with side effects, or start services to answer; when an answer would need one of these, say what you would run and ask first. When the question turns out to describe something broken, say so and switch to `rumo-debug`.

## 1. Pin The Question

Name the exact target (file, symbol, feature, or flow) and why the user is asking: about to change it, reviewing it, debugging nearby, or new to it. Read that purpose from the conversation instead of quizzing the user. It decides the depth: a change needs the call chain and the contracts it must keep; onboarding needs the overall shape first. When the target is ambiguous, state your reading in one line and continue; the user can redirect.

## 2. Read The Real Path

Find the entry point (route, command, event, screen, job) and follow the calls through the layers that matter for the question. Read the code yourself; do not infer behavior from names, comments, or file layout alone. Note the data shapes passed between parts, who owns each piece of state, and where configuration changes the behavior. Stop reading once the question is answered.

## 3. Find The Why

Look for the reasons in the record, not in plausible stories:

- `git log --follow` on the main files and `git blame` on the lines in question, then the commit messages behind them.
- Pull request or issue discussion when the repository has a remote you can query, such as `gh pr view <number>`.
- Decision records, plans, and design notes in the repository (`rumo-plan` keeps them as ADRs), and comments that state a constraint.

When the record says nothing, report that as the finding and label any explanation you offer as inference. Never invent a history, an author's intent, or a past incident.

## 4. Answer

- Start with the smallest complete answer: one or two plain sentences that say what the thing is and what it does, in words a colleague would use out loud. Then stop or go one layer deeper as the question needs.
- When more is needed, use only the parts that apply: what it is, how it runs (the path from input to effect), where it lives (`file:line`), why it has this shape (with the commit, PR, or record), and the traps a person changing it would hit.
- Give each concept one name and keep it. Explain mechanisms concretely; do not substitute metaphors or labels such as "the key insight".
- Draw a Mermaid diagram only when three or more parts interact and the picture is faster than the sentences; keep each diagram small.
- Mark where each claim comes from: code you read (`file:line`), a run, the history, or inference.
- End by offering the next layer or a nearby question worth asking; do not start changing code.

## Stop Conditions

- The answer depends on runtime state you cannot read without side effects, such as a production database or a running service: say what is missing and ask.
- The history or the code contradicts what the user believes: show both and let the user decide; do not smooth it over.

## Shortcuts And Rebuttals

| Tempting shortcut | Why it fails |
| --- | --- |
| "The function name says what it does." | Names drift; read the body and its callers. |
| "It was probably done this way for performance." | An unrecorded reason is inference; label it or find the commit. |
| "A full tour is more helpful." | Depth beyond the question buries the answer; offer the next layer instead. |
