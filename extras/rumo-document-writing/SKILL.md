---
name: rumo-document-writing
description: Use when drafting, revising, splitting, formatting, or quality-checking formal Word delivery documents such as designs, reviews, tests, acceptance materials, deployment manuals, operations manuals, interface documents, and technical reports. Do not use for repository Markdown, code comments, or other in-repo prose; use rumo-prose instead.
---

# Document Writing

This skill governs evidence, product-boundary wording, formal structure, and delivery quality. It does not create or edit DOCX files itself: use a Word-capable tool the client provides, such as a docx skill, or an installed library or converter such as python-docx or pandoc. When none is available, say so and stop rather than delivering a different format.

Follow the requested audience, language, organization template, terminology, and source document. When those rules are project-specific, resolve them through `rumo-project-profile`.

- Preserve existing images, tables, page breaks, headers, footers, numbering, styles, and tracked requirements unless the user asks to redesign them.
- Translate source and code evidence into stable product concepts without leaking local paths, generation notes, Markdown markers, temporary filenames, or implementation details outside scope.
- Distinguish design, implementation, test, deployment, and field-acceptance evidence.
- Do not claim verification or acceptance that was not actually obtained.
- Render the final DOCX to page images, for example by converting it to PDF with LibreOffice in headless mode, and inspect every page for overflow, clipping, broken tables, orphan headings, inconsistent spacing, and unreadable diagrams. When no renderer is available, report the layout as not inspected.

Deliver the final document and summarize material changes, evidence used, and remaining acceptance boundaries.
