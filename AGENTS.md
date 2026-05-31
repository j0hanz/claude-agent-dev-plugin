# Agent Dev Plugin Instructions

Claude Code plugin for authoring and testing agents, skills, and hooks.

## Package Manager

Use **npm** — `npm install`.

```bash
npm install
uv sync
```

## Dependency Locations

- Node modules: `node_modules/`
- Python virtual environment: `.venv/` (managed by uv)

## File-scoped commands

| Task        | Command                               |
| ----------- | ------------------------------------- |
| Lint (JS)   | `npx eslint <file.mjs>`               |
| Format (JS) | `npx prettier --check <file>`         |
| Test (JS)   | `node --test <path/to/file.test.mjs>` |
| Lint (Py)   | `ruff check <file.py>`                |
| Format (Py) | `ruff format <file.py>`               |
| Test (Py)   | `python -m pytest <path/to/test.py>`  |
| All tests   | `npm test`                            |
| All Python  | `npm run test:python`                 |

## Key Conventions

- **Hook routing:** All hooks dispatch via `hooks/runner.mjs <domain> <action>`, which dynamically imports `hooks/handlers/<domain>.mjs` and calls `action()`. Never put hook logic outside this pattern.
- **Hooks are additive only:** Handlers must write to stdout for context injection and exit 0. No blocking, no user-facing prompts, no permission gates.
- **Skills layout:** Each skill lives in `skills/<name>/SKILL.md` with optional `references/`, `scripts/`, `agents/`, and `evals/` subdirs. Root-level `agents/<name>.md` are project-wide agents not scoped to a single skill.
- **Skill editing:** Use the skill's own files as the source of truth — don't copy patterns from sibling skills.
- **Hook handlers use `.mjs`** (native ESM). Skill scripts outside hooks may use `.js`. No TypeScript, no transpile step.
- **Extension points:** `commands/<name>.md` adds slash commands; `monitors/monitors.json` registers monitors; `bin/` contains CLI utilities.

## Commit Attribution

AI commits MUST include a `Co-Authored-By:` trailer.
Example: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
