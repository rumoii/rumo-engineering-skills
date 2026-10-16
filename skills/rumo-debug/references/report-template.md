# Root-Cause Report Template

Use this structure for final diagnosis. Keep it concise and evidence-led.

```markdown
**Root Cause**
<One or two sentences that explain the actual cause, not just the symptom.>

**Evidence**
- Frontend: `<file>` calls `<method> <endpoint>` from `<page/menu>`.
- API contract: request `<params/body/path/header>` maps `<frontend fields>` to `<backend DTO/VO>` and response shape is `<ResponseData/ResponseList/file/etc>`.
- Backend: `<controller method>` -> `<service/biz>` -> `<mapper/sql/table>`.
- Runtime: `<host>` `<log file>` around `<timestamp>` shows `<short paraphrase>`.
- Data/middleware: `<table/key/topic>` contains `<state>` that confirms the cause.
- Responsibility: `<platform | client | unclear>` because `<server-created/notified | client-executed-without-server-row | evidence gap>`.

**Impact**
<Affected product/module/users/terminal scope. State unknowns explicitly.>

**Fix Boundary**
<frontend | backend | data/config | deployment | middleware | terminal-client> and the specific files/tables/config likely needing change.

**Next Step**
<Smallest action to fix or confirm, such as patch method X, add guard Y, clean invalid test data with approval, or reproduce with request Z.>
```

Rules:

- Do not include plain-text credentials.
- Do not paste long log blocks; paraphrase and quote only short identifiers, timestamps, and error names.
- If the conclusion is probable but not proven, label it `Likely root cause` and list the missing evidence.
- If remote checks were not run because credentials are missing, say `Remote evidence blocked`, ask the user to configure credentials first, include OS/shell-specific setup commands, and include the exact read-only command to rerun.
