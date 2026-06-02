# Agent Dev Plugin Instructions

A Claude Code plugin for authoring and maintaining agents, skills, and hooks.

## Package Managers

- **Node.js:** `npm install`, `npm test`, `npm run lint` (Node ≥22 required)
- **Python:** `pip install pytest pyyaml jsonschema` into `.venv` — use `python -m pytest` for tests

## Dependency Locations

- Node modules: `node_modules/`
- Python virtual environment: `.venv/`

## File-Scoped Commands

| Task            | Command                                    |
| --------------- | ------------------------------------------ |
| Lint (JS)       | `npx eslint path/to/file.mjs`              |
| Lint + fix      | `npx eslint --fix path/to/file.mjs`        |
| Format check    | `npx prettier --check path/to/file.mjs`    |
| Test (Node)     | `node --test path/to/file.test.mjs`        |
| Test (Python)   | `python -m pytest path/to/test_file.py -q` |
| Validate plugin | `npm run validate`                         |

## Key Conventions

- **Hook routing:** All hooks dispatch via `hooks/runner.mjs <domain> <action>`, which imports `hooks/handlers/<domain>.mjs` and calls the exported `<action>` function. Handlers receive stdin as parsed JSON; return a string, object, or nothing. Register new events in `hooks/hooks.json`.
- **ESM only:** All JS files use ES modules (`import`/`export`). No CommonJS `require()`.
- **Test registration:** Node tests use `node --test` with an explicit file list — add new `*.test.mjs` paths to the `test:node` script in `package.json`. Python tests added under `skills/*/tests/` or `skills/skill-builder/tests/` are picked up by the `test:python` script automatically.
- **Skill structure:** Each skill lives in `skills/<name>/` with a `SKILL.md` and optional `references/`, `scripts/`, `evals/` subdirs. Never flatten skill files into `skills/`.
- **Plugin validation:** Run `npm run validate` before committing — it checks plugin structure and manifest compliance via `bin/validate-plugin.mjs`.
- **Telemetry:** Hook debug output is written to `.claude/telemetry.log`. Set `CLAUDE_HOOKS_DEBUG=1` to enable verbose hook tracing.

## Commit Attribution

Every AI commit MUST include a `Co-Authored-By:` trailer. Example:

```text
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
