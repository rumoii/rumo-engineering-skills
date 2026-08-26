# Local project profile

This directory is a private, user-maintained project profile.

Start with `project.json`. Add repository names and paths after the project
exists, then fill in only the sections needed by the skills you use:

- `frontend.json`: frontend roots, framework, commands, proxy, and browser entrypoints.
- `backend.json`: build system, modules, artifacts, and service mapping.
- `runtime.json`: hosts, ports, logs, install roots, and runtime actions.
- `data.json`: databases, caches, queues, and read-only probe metadata.
- `documents.json`: document types, templates, and writing conventions.
- `references/`: detailed project notes linked from the JSON files.

Keep real credentials outside tracked files. Use environment variables or a
local ignored credentials file. The generic skills continue to work when this
profile is empty or only partially filled.
