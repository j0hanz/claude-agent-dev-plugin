# Agent Maintenance Reference Guide

This guide contains everything you need to draft, refactor, and wire `AGENTS.md` files (and their variants like `CLAUDE.md`, `GEMINI.md`, etc.).

**Format rule:** every section body is `key: value` lines (markdown-kv) — not prose paragraphs, not nested bullets-of-bullets. One fact per line. Tables stay tables (commands, workspace layout).

**Order rule:** Hard Rules come immediately after the H1 + description, before Toolchain/Conventions. Attribution is the only thing that goes last.

## 1. Generating the Skeleton

Don't hand-write or hand-copy a template — generate one. `scripts/run.py scaffold-agents-md` holds the skeleton (Hard Rules block, marker, Commit Attribution) and the per-language defaults (`Config.LANGUAGE_DEFAULTS`, `Config.HARD_RULES_TEXT`) as data, so the LLM never re-derives or retypes boilerplate.

```bash
python scripts/run.py scaffold-agents-md \
  --language <node|python|go|rust|java|dotnet|bun> \
  --purpose "<one sentence — what this repo does>" \
  --commit <strict|relaxed|minimal> \
  --maturity <production|development> \
  --testing <always|touched-files|not-enforced> \
  [--pm "<override>"] [--set key=value ...] \
  [--out AGENTS.md]
```

Output: H1, `purpose:`, `## Hard Rules` (full sentences + marker), `## Package Manager`, `## Dependency Locations`, `## File-Scoped Commands` table, language-appropriate defaults under `## Key Conventions`, `## Commit Attribution` (substitute `<Model Name>` dynamically with the active model, e.g., `Gemini 3.5 Flash` or `Claude 3.5 Sonnet`).

After running it:

1. Override any default Phase 1 found wrong — re-run with `--pm`/`--set key=value`, don't hand-edit a wrong default into something else wrong.
2. Review the scaffolded `## Key Conventions` defaults and refine/extend them (to have 3-7 real `key: value` lines) grounded in the actual repo (see §2.5).
3. No language match (PHP, Ruby, etc.)? Pick the closest `--language`, then override every toolchain value with `--set` — treat the defaults as scratch, not fact.

### Shapes the script doesn't cover

Monorepos, package-level overrides, and polyglot repos don't fit one `--language` slot — assemble these sections by hand, still in markdown-kv:

**Monorepo** — add on top of the generated skeleton:

```markdown
## Workspace Layout

| Package     | Path          | Purpose       |
| ----------- | ------------- | ------------- |
| `@acme/api` | `apps/api`    | HTTP API      |
| `@acme/db`  | `packages/db` | Prisma client |

## Cross-Package Commands

filter: `pnpm --filter @acme/api test`
all: `pnpm -r build` (uses Turbo cache)
note: each package may have its own `AGENTS.md` with overrides
```

**Package-level override** (only when a package's tooling genuinely differs from root — don't duplicate root sections, reference them):

```markdown
# @acme/api Agent Instructions

See root `/AGENTS.md` for shared setup and workspace commands.

## Override: Test Runner

runner: Mocha, not Jest
test: `mocha --require ts-node/register src/**/*.test.ts`
test-one-file: `mocha --require ts-node/register src/auth/test_login.test.ts`
```

**Polyglot** — run the scaffold once per subsystem's dominant language, then merge into one file under per-subsystem headings (or split into `backend/AGENTS.md` + `frontend/AGENTS.md` + a root `AGENTS.md` with only `## Shared Conventions` if the toolchains diverge enough to make one file noisy):

```markdown
## Shared Conventions

errors: every error includes a unique code + user-facing message
testing: both suites use the same coverage threshold (80% minimum)

## Backend (Python + FastAPI)

pm: uv — `uv sync`, `uv run pytest`

## Frontend (TypeScript + React)

pm: pnpm — `pnpm install`, `pnpm test`
```

## 2. Anti-Patterns (What to Cut)

When refactoring, aggressively remove these:

- **Intros/Warmups:** Delete "Welcome to..." or "This document explains...". Agents don't need warmups.
- **Linter/Formatter Rules:** Delete "Use 2 spaces", "Prefer const". Let the linter enforce these.
- **Auto-discovered Tools:** Don't list MCP servers or tools the agent already knows about.
- **Full Project Builds:** Prefer file-scoped commands (e.g., `tsc --noEmit single-file.ts`) over `pnpm build`.
- **Generic Instructions:** Delete "Write clean code", "Test thoroughly". Be specific or delete.
- **Prose Explanations:** Convert paragraphs into concise bullets. Agents skim.
- **Stale TODOs:** Delete "TODO: migrate to Vite". Agents will try to action them immediately.
- **Repeating README/CONTRIBUTING:** Link to them instead (`See CONTRIBUTING.md for branch naming.`).
- **File Trees:** Point to 2-3 critical files instead of pasting a massive `ls` output.
- **Auto-generated Boilerplate:** Delete anything not specifically grounded in the _current_ repo.

## 2.5 Key Conventions: Good vs. Bad Examples

The "Key conventions" section should capture patterns the linter can't enforce. Here's what works and what doesn't:

### Bad Conventions (Vague, Unverifiable)

```markdown
- Use descriptive names
- Follow best practices
- Be careful with error handling
- Test everything
- Keep it simple
- Think about performance
```

**Why these fail:**

- "Descriptive names" — Can't verify. Descriptive for what? `login_handler` vs. `auth` vs. `handleLogin`?
- "Best practices" — Vague. Which practices? A list of 100?
- "Be careful" — Subjective. No way to test compliance.
- "Test everything" — Undefined. Unit only? Integration? End-to-end?
- "Keep it simple" — Can't measure. Simple by what standard?

### Good Conventions (Specific, Verifiable)

```markdown
file-naming: handlers end `.handler.ts`, utilities end `.util.ts` — e.g. `login.handler.ts`
errors: all inherit `AppError` (`src/errors.ts`); include `statusCode` + `userMessage`
testing: every exported function has a test; every async function has an integration test
migrations: never edit applied ones; create with `pnpm migrate create --name feature_name`
api-pattern: routers call services; services return data, never HTTP responses
dependency-injection: constructor injection only — no `@Autowired`, no service locators
```

**Why these work:**

- Specific file patterns (`*.handler.ts`, `*.util.ts`)
- Clear class/interface inheritance (`extends AppError`)
- Measurable coverage rules ("every async function")
- Concrete locations (`src/errors.ts`)
- Clear examples and counter-examples
- Verifiable from code review

### The 3-7 Bullet Rule

Aim for **5-7 conventions**:

- **Too few (<3):** Not enough guidance; agents have to guess
- **Sweet spot (5-7):** Comprehensive but scannable; agents can remember them
- **Too many (>7):** Overwhelming; move to detailed docs and link

If you have 10+ conventions, that's a signal that:

1. Your codebase has too many unwritten rules, OR
2. You should document them in `docs/CONVENTIONS.md` and link from AGENTS.md

### Writing Checklist

For each convention, verify:

- [ ] **Specific:** Can someone verify compliance by reading code?
- [ ] **Location aware:** Include file/folder if applicable (e.g., `src/errors.ts`)
- [ ] **Actionable:** An agent could follow this rule without asking for clarification
- [ ] **Not a linter rule:** Linter configs should enforce, not AGENTS.md
- [ ] **Not generic:** Avoid "write clean code", "be careful", "best practices"

## 3. Scripts Reference

Helper scripts are available via `scripts/run.py`:

```bash
python scripts/run.py <command> [args]
```

- `analyze-all [target_dir] [--max-depth 3]` — Run environment detection, dependency listing, and structure scan sequentially
- `analyze-env [target_dir]` — Detect package manager, test runner, linter, monorepo structure
- `scan-structure [target_dir] [--max-depth 3]` — Output directory tree (respects .gitignore)
- `scaffold-agents-md --language L --commit C --maturity M --testing T [--purpose P] [--pm PM] [--set k=v ...] [--out FILE]` — Print/write a complete AGENTS.md skeleton, Hard Rules first (see §1)
- `lint-agents-md <path_to_AGENTS.md>` — Validate AGENTS.md length, filler text, commit attribution
- `wire-agents <source_file> <target1> [target2...]` — Write one-line redirect stubs in each target pointing to the source

**Hook integration:** `scripts/run_lint.sh` is a thin shell wrapper that runs `lint-agents-md` using `$CLAUDE_PLUGIN_ROOT` and `$CLAUDE_PROJECT_DIR` environment variables. It is intended for use in Claude Code hooks (e.g., `PostToolUse`) to automatically lint the AGENTS.md after edits. Invoke it directly only if those env vars are set.

## 4. File Setup & Wiring

Create one canonical `AGENTS.md`. Every other agent-specific filename is a **one-line redirect stub** — never a copy, symlink, or hardlink. A full copy means every tool that loads `CLAUDE.md`/`GEMINI.md` re-spends tokens on content already in `AGENTS.md`; a stub costs one line and the agent reads the real file only when it needs to.

```bash
python scripts/run.py wire-agents AGENTS.md CLAUDE.md GEMINI.md
```

Each target file ends up containing exactly:

```markdown
# See [AGENTS.md](AGENTS.md)
```

| Agent / tool           | File it looks for                   |
| ---------------------- | ----------------------------------- |
| OpenAI Codex / generic | `AGENTS.md`                         |
| Claude Code            | `CLAUDE.md`                         |
| Gemini CLI             | `GEMINI.md`                         |
| Cursor                 | `.cursorrules` or `.cursor/rules/*` |

**Cursor:** `.cursorrules` requires plain text and Cursor doesn't follow markdown links — use the same one-line stub format anyway; if Cursor must have the full body, that's the one exception to the no-copy rule.

## 5. Refactoring Examples

### Before (Bloated)

```markdown
# Welcome to FooBar

This project is built with TS, React, and PG. We love clean code.

- Use 2 spaces
- Always use semicolons
- Run `pnpm test` to run all tests
```

### After (Lean)

```markdown
# Agent Instructions

purpose: TS/React/Postgres app

## Hard Rules

commit: free-form messages, Co-Authored-By required
maturity: development — breaking changes fine
testing: touched-files only

<!-- codebase-init:hard-rules v1 commit=relaxed maturity=development testing=touched-files -->

## Package Manager

pm: pnpm

## File-Scoped Commands

| Task | Command                          |
| ---- | -------------------------------- |
| Test | `pnpm jest path/to/file.test.ts` |

## Commit Attribution

Co-Authored-By: <Model Name>
```
