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

When `rumo-incremental-deploy` needs reusable project facts, a project may add
an illustrative entry such as this to `runtime.json` and adapt the field names
to its maintained conventions:

```json
{
  "deployments": [
    {
      "id": "application",
      "purpose": "development",
      "host_env": "PROJECT_DEPLOY_HOST",
      "user_env": "PROJECT_DEPLOY_USER",
      "destination": "",
      "services": [],
      "backup_rule": "",
      "restart_command": "",
      "verification_commands": [],
      "rollback_command": ""
    }
  ]
}
```

Keep unknown values empty and use environment-variable names rather than
credentials or live host values in a shared profile.

Keep real credentials outside tracked files. Use environment variables or a
local ignored credentials file. The generic skills continue to work when this
profile is empty or only partially filled.
