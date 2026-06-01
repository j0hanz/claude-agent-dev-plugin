---
description: Diagnose and fix a bug using structured root-cause analysis
argument-hint: <bug description or error message>
---

# Fix a Bug

Diagnose and fix: $ARGUMENTS

Applies structured debugging (diagnose skill) to find the root cause, then delegates the fix to the coder agent. Finds the actual failure path before touching code.

Current branch: !`git branch --show-current`
Recent changes: !`git diff HEAD --name-only`
Test output: !`npm test 2>&1 | tail -30`

## Usage

- You have a concrete error message or failing test and need root-cause analysis
- A regression appeared after a recent change and you need to trace where it broke
- A bug is subtle enough that guessing the fix would likely miss the actual cause

Prefer `/coder` when the bug location is already known. Prefer `/explore` when unsure if the behavior is actually a bug.

## Execution Steps

1. Invoke the diagnose skill: `Skill("diagnose", "$ARGUMENTS")`
2. Identify the root cause: file, line, and failure mode
3. Spawn coder agent: "Fix the bug at `<file>:<line>`. Root cause: `<diagnosis>`. Run tests after fix."
4. Verify fix — confirm the failure is gone
5. Check for regressions in related tests

Run: !`npm test 2>&1 | tail -20`

> **Note**: Substitute `npm test` with your project's test command (`pytest`, `go test ./...`, `cargo test`, etc.).

## Troubleshooting

**Diagnose skill can't find root cause** — Provide a stack trace or exact failing assertion instead of a high-level description.

**Fix applied but tests still fail** — Root cause may have been a symptom. Re-run diagnose with the new failure as input.

**New failures appear after fix** — Stop. Revert with `git diff HEAD` to confirm scope, then re-diagnose with the regression as input.

**`npm test` not found** — Check `package.json` scripts for the correct test command.

## Success Criteria

- Root cause identified (not just symptom fixed)
- Fix is minimal and targeted — no unrelated changes
- All tests pass after the fix
- No regressions introduced
