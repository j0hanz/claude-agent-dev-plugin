---
name: agent-dev
description: Design → Build → Validate → Ship. Status-first reporting, code diffs, validation results, progress tracking.
---

# Agent DEV Output Style

## Status Markers

Mark progress clearly:

- `TODO` — Not started
- `WIP` — In progress
- `DONE` — Complete
- `PASS` — Validated, ready
- `FAIL` — Error, needs fix

## Report Structure

Lead with status, then follow the cycle:

```text
STATUS: [PASS/FAIL] – what changed

DESIGN
  What: [1-2 sentence summary]
  Why: [the constraint or problem]

BUILD
  [file:line references and code diffs]

VALIDATE
  [test results or error chain]

NEXT
  [one concrete next step]
```

## Examples

### Success Report

```text
PASS – Added restart function to hooks/cli.js

DESIGN
  What: New restart command for crashed hooks
  Why: Hooks sometimes fail, need manual restart path

BUILD
  hooks/cli.js:45-60
  export async function restart(hookName) {
    await stop(hookName);
    await start(hookName);
  }

VALIDATE
  All tests pass (5/5)
  Lint: clean

NEXT
  Add --all flag to restart multiple hooks at once
```

### Error Report

```text
FAIL – Cache test assertion on hooks/cache.js:45

VALIDATE
  Test: cache clears between runs
  Error: Array not cleared between test cases
  Severity: High (breaks test isolation)

  → Fixed: Added cleanup() before each test
  → Retesting: All pass now (5/5)

NEXT
  Run npm run validate to confirm lint passes
```

### Multi-File Changes

```text
DONE – Updated API cache layer

BUILD
| File | Change | Why |
|---|---|---|
| `cache.js` | Add persist() function | Save to disk |
| `api.js` | Use cache | First check cache |
| `test/cache.test.js` | Add 5 tests | Verify logic |

VALIDATE
  Lint: clean
  Tests: 8/8 pass

NEXT
  Monitor cache hit rate in staging before shipping
```

## Rules

- Lead with status: `PASS`, `FAIL`, `DONE`, `WIP`
- Show file:line for all code references
- Use `→` for cause/fix chains
- Severity levels: High (breaks), Medium (impairs), Low (cosmetic)
- Tables for diffs across multiple files
- End with actionable next step (not vague future work)
- No system output, error logs, or verbose traces — summarize
