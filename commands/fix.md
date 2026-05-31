---
description: Diagnose and fix a bug using structured root-cause analysis
argument-hint: <bug description or error message>
---

# Fix a Bug

Diagnose and fix: $ARGUMENTS

First applies structured debugging (diagnose skill) to find the root cause, then delegates the fix to the coder agent. Avoids guessing — finds the actual failure path before touching code.

Current branch: !`git branch --show-current`
Recent changes: !`git diff HEAD --name-only`
Test output: !`npm test 2>&1 | tail -30`

## When to Use

- You have a concrete error message or failing test and want root-cause analysis before touching code
- A regression appeared after a recent change and you need to trace where it broke
- A bug is subtle enough that guessing the fix would likely miss the actual cause
- You want structured diagnosis (symptom → cause → fix) rather than trial-and-error

Prefer `/coder` when the bug location is already known and the fix is straightforward. Prefer `/explore` when you're not sure if the behavior is actually a bug.

## Execution Steps

1. Invoke the diagnose skill: `Skill("diagnose", "$ARGUMENTS")`
2. Identify the root cause file, line, and failure mode
3. Once root cause is confirmed, spawn coder agent: "Fix the bug at <file>:<line>. Root cause: <diagnosis>. Run tests after fix."
4. Verify fix — run the test suite and confirm the failure is gone
5. Check for regressions in related tests

Run: !`npm test 2>&1 | tail -20`

> **Note**: This command assumes `npm test` is the project test runner. For non-Node projects, substitute the appropriate command (e.g., `pytest`, `go test ./...`, `cargo test`).

## Troubleshooting

**Diagnose skill can't find the root cause** — Provide a stack trace or the exact failing assertion rather than a high-level description. The more specific the input, the better the diagnosis.

**Fix is applied but tests still fail** — The root cause may have been a symptom. Re-run the diagnose step with the new failure output as input.

**New failures appear after the fix** — Stop. Revert with `git diff HEAD` to confirm scope, then re-diagnose with the regression as the new input.

**`npm test` not found** — Check `package.json` scripts for the correct test command and substitute it in step 4.

## Success Criteria

- Root cause identified (not just symptom fixed)
- Fix is minimal and targeted — no unrelated changes
- All tests pass after the fix
- No regressions introduced

A targeted fix beats a broad rewrite — diagnose first, touch only what broke.
