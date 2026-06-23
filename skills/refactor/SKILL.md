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

Build a mental model before touching code:

- **Blast Radius:** Use `Grep` to find all callers and dependencies.
- **Invariants:** Identify hidden logic requirements.
- **Tests:** Verify current tests exist and pass. **Gate:** run the suite now and paste the actual output (exit code + pass/fail counts) as the green baseline — a claim that "tests pass" without pasted output does not satisfy this step. If the path being touched has no test covering it, write a characterization test first (see Critical Rules) and confirm IT passes before treating anything as a safety net.

## Step 2: Pain Point Mapping

**action: Map Pain Points**
If vague, ask "What is the hardest part of working with this code?" and confirm via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually. Ground options in the pain-point table below rather than generic phrasing — if the code shows symptoms matching 2+ rows, surface those as the real options instead of inventing a placeholder second guess:

1. ✅ **Recommended** — [Diagnosis] based on [the table row whose symptom best matches what you observed: nesting, duplication, coupling, naming].
2. **Alternative** — [a second table row whose symptom is also plausible] + the reason it might be the better fit.

**MANDATORY**: If the pain point is vague or complex, you MUST read `references/smell-catalog.md` to accurately diagnose the issue. **Skip it** if the pain point is a single, obvious mechanical change (e.g., a plain rename) — the table below is enough.

| Pain                   | Likely Problem      | Rationale                                 |
| :--------------------- | :------------------ | :---------------------------------------- |
| \"Hard to add cases\"  | Missing Abstraction | Use Strategy, Enum, or Factory.           |
| \"Hard to understand\" | Poor Naming / Bloat | Rename, extract helpers.                  |
| \"Copy-pasted\"        | Duplication         | Extract shared utility (DRY).             |
| \"Tests breaking\"     | Hidden Coupling     | Dependency injection, concern separation. |

## Step 3: Priority & Risk

Risk tier follows directly from the Step 2 diagnosis — a "Missing Abstraction" or "Hidden Coupling" diagnosis is High Risk; "Poor Naming" or simple duplication is Low/Medium.

1. **Low Risk (First):** Rename misnomers, replace magic literals, remove dead code, early returns. **DO NOT load `patterns.md` for these changes.**
2. **Medium Risk:** Split functions, extract classes, introduce types/interfaces.
3. **High Risk (Confirm First):** Reorganize modules, change public API signatures, apply Observer/Strategy patterns. **MANDATORY**: Before applying a pattern, read `references/patterns.md`.

## Step 4: Hidden Bug Protocol

If a bug is discovered during refactoring: **STOP.**

1. Surface the bug (trigger, behavior, fix).
2. **NEVER** fix it in the same turn as the refactor.
3. Leave the buggy line intact. Fix only in a separate, dedicated step (invoke `diagnose`).

## Step 5: Small, Verified Steps

- **Checkpoint:** Commit or stash before starting.
- **Cycle:** One change → Confirm (read diff) → Run tests → Confirm typecheck.
- **Automated Tools:** Run `prettier`, `eslint --fix`, `ruff format`, or `gofmt` before manual edits.

## Step 6: Communication (Mandatory Output)

```markdown
## Changes

**What changed:** [List renames, extractions, reorganizations]
**Why:** [Problem solved / Benefit gained]
**Deliberately NOT changed:** [Preserved scope / Justification]
```

**next skills:**

- `architecting`: If scope creeps beyond single-file/function (see description for the boundary).
- `diagnose`: If a pre-existing bug is discovered during the refactor that requires systematic isolation.
- `verification-before-completion`: Once the structural changes are complete, to ensure behavior is preserved.

## Critical Rules

- **NEVER** mix behavior changes with structural changes.
- **NEVER** extract solely on structural similarity (Incidental Duplication).
- **NEVER** change public signatures without test coverage.
- **NEVER** refactor an untested critical path. Write characterization tests first.
- **NEVER** introduce an abstraction (interface, factory, strategy map) before the third real occurrence — two similar blocks is not yet a pattern.
- **NEVER** rename and change logic in the same edit, even when both touch the same line — split into two diffs so the diff itself proves no behavior changed.

## Transition

Invoke `verification-before-completion` after the final test pass.
