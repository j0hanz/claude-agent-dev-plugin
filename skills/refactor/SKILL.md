---
name: refactor
description: "Improve code structure without changing behavior, scoped to a single file or function. Focus on readability and testability. Not for changes spanning multiple files or module boundaries (see architecting). Trigger on: 'clean up', 'refactor', 'simplify code', 'improve this function's structure', 'modernize', 'code smell', 'extract function', 'rename symbol'."
disable-model-invocation: false
---

# refactor

Improve structure without changing behavior. Focus on readability, testability, and extensibility.

## Process Flow

```
Start: Refactor Request
  -> 1. Baseline Analysis (grep, invariants, tests)
  -> 2. Pain Point Mapping (smell catalog)
  -> 3. Priority & Risk (low -> med -> high)
  -> Execution Cycle: Automated Tools -> Small Change -> Verify (diff, tests, typecheck)
       -- bug discovered? yes --> diagnose (handoff)
       -- bug discovered? no  --> next change (loop)
  -- all changes complete --> verification-before-completion (handoff)
```

## Step 1: Baseline Analysis

Understand the code first:

- **Blast Radius:** `Grep` callers and dependencies.
- **Invariants:** Find hidden rules.
- **Tests:** Run tests and paste the exact output (exit code + pass/fail). Saying "tests pass" is not allowed. If there are no tests, write one and prove it passes first.

## Step 2: Pain Point Mapping

**Action:** Ask "What is the hardest part?" using `AskUserQuestion`. Pick the best match from the table below. Do not make up new options.

**MANDATORY:** If the problem is hard, read `references/smell-catalog.md`. Skip this if it is a simple rename.

| Pain                 | Problem             | Fix                             |
| :------------------- | :------------------ | :------------------------------ |
| "Hard to add cases"  | Missing Abstraction | Use Strategy, Enum, or Factory. |
| "Hard to understand" | Poor Naming / Bloat | Rename, extract helpers.        |
| "Copy-pasted"        | Duplication         | Extract shared code.            |
| "Tests breaking"     | Hidden Coupling     | Dependency injection.           |

## Step 3: Priority & Risk

Match risk to your Step 2 problem.

1. **Low Risk:** Rename, remove dead code, early returns. (Do NOT read `patterns.md`).
2. **Medium Risk:** Split functions, extract classes.
3. **High Risk:** Change APIs, move modules, add patterns. **MANDATORY:** Read `references/patterns.md` first.

## Step 4: Hidden Bug Protocol

If you find a bug: **STOP**.

1. Report the bug.
2. **NEVER** fix it during a refactor.
3. Leave the buggy line alone. Fix it later using `diagnose`.

## Step 5: Small, Verified Steps

- **Save:** Commit or stash first.
- **Cycle:** Edit → Read diff → Run tests → Check types.
- **Format:** Auto-format (`prettier`, `eslint --fix`, `ruff format`, or `gofmt`) before you edit manually.

## Step 6: Communication

Output exactly this format:

## Changes

**What:** [List changes]
**Why:** [Problem solved]
**Left alone:** [What was not changed and why]

**Next Skills:**

- `architecting`: For changes across multiple files.
- `diagnose`: To fix bugs you found.
- `verification-before-completion`: Run this after your final tests pass.

## Critical Rules

- **NEVER** mix behavior changes with structural changes.
- **NEVER** extract code just because it looks similar.
- **NEVER** change public APIs without tests.
- **NEVER** touch untested critical code. Write tests first.
- **NEVER** build an abstraction for just two cases. Wait for three.
- **NEVER** rename and change logic at the same time. Do it in two separate steps.

## Transition

Run `verification-before-completion` when done.
