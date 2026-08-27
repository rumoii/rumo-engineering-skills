# Contributing

Contributions should keep every skill independent of a specific company,
product, repository layout, host, or deployment environment.

## Requirements

- Use the `rumo-` namespace and lowercase hyphen-case for skill directories.
- Keep each `SKILL.md` activation description concrete and discriminating.
- Keep private project facts in a local Profile, never in this repository.
- Do not commit credentials, private keys, certificates, customer data, or
  internal infrastructure details.
- Add or update focused tests when changing scripts or deterministic rules.
- Preserve unrelated files and avoid generated dependencies such as
  `node_modules`.

## Validate changes

Windows:

```powershell
py -3 scripts\verify_skills.py
py -3 -m unittest discover -s scripts\tests -p "test_*.py"
py -3 scripts\run_auxiliary_tests.py
git diff --check
```

Linux and macOS:

```bash
python3 scripts/verify_skills.py
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
python3 scripts/run_auxiliary_tests.py
git diff --check
```

Pull requests should explain the user scenario, changed behavior, verification
performed, and any environment or acceptance boundary that was not exercised.
