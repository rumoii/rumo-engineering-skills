---
name: rumo-imagegen
description: Generate and save one raster image through a user-configured OpenAI-compatible image endpoint. Use only when the user explicitly selects this configured service; do not use for diagrams, screenshots, or when a first-party image tool is more appropriate.
---

# Image Generation

Requires Node.js 18 or later and these current-process variables:

- `RUMO_IMAGE_ENDPOINT`: complete image-generation endpoint.
- `RUMO_IMAGE_API_KEY`: bearer token.

Optional defaults are `RUMO_IMAGE_MODEL`, `RUMO_IMAGE_SIZE`, and `RUMO_IMAGE_QUALITY`. Project-specific endpoint and model guidance may come from [`rumo-project-profile`](../rumo-project-profile/SKILL.md).

Resolve an exact output path, create a private temporary UTF-8 prompt file, and run `scripts/generate.mjs`. The script never overwrites an existing output and never prints the API key.

If the configured endpoint uses plain HTTP, explain that the token and prompt are unencrypted in transit and obtain explicit acceptance before the API call. Use `--allow-insecure-http` only after that acceptance.

```powershell
node <skill-dir>\scripts\generate.mjs --prompt-file <prompt-file> --output <absolute-output.png>
```

```bash
node <skill-dir>/scripts/generate.mjs --prompt-file <prompt-file> --output <absolute-output.png>
```

A direct request authorizes one generation. Do not automatically retry, create variants, or switch providers. Verify the output signature and file size, inspect the image when useful, delete the temporary prompt file, and distinguish file creation from visual acceptance.
