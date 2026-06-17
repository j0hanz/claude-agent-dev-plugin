---
name: test-driven-development
description: "Test-driven development. Trigger on 'TDD', 'test-first', 'write tests', 'write a function', 'implement this', 'add feature', 'build this'. Also trigger proactively before any non-trivial implementation begins, even when TDD is not explicitly requested. Defines strict red-green-refactor procedures for agent-driven development."
user-invocable: true
---

# test-driven-development

Autonomous TDD execution. **HARD GATE:** No implementation code WITHOUT a failing test.

## Step 0: Confirm

This will start an autonomous session (~N calls). Proceed? Wait for explicit user confirmation before writing any test.

## 0. Pre-TDD: Interface Definition

Document the public surface before writing tests:

1. **Signatures:** `name(params) -> return_type`
2. **Error Cases:** Explicit exception types or error returns.
3. **Usage Examples:** 2-3 realistic scenarios.
4. **Target:** Identify test file path (e.g., `tests/test_NAME.py`).

## 1. Execution Loop: RED → GREEN → REFACTOR

Execute exactly ONE scenario per cycle. **NEVER** batch tests (No horizontal slicing).

### Phase 1: RED (The Failing Test)

1. Write the simplest possible test for a single core behavior.
2. **Stubbing:** Write the **minimal** stub (e.g., `pass` in Python, `return null` in TS) to allow the test to compile and run. **DO NOT** implement any logic yet.
3. **Run Test:** Execute the runner.
   - **Runner Integration:**
     - **pytest:** Look for `FAILED` or `ERROR`. Check `Captured stderr` for logs.
     - **vitest/jest:** Look for `FAIL`. Check `AssertionError` diffs.
     - **go test:** Look for `--- FAIL`.
4. **Analyze Failure:**
   - **Environment Fail:** (Missing module/import) → Fix environment → Rerun.
   - **Assertion Fail:** (Correct RED) → Proceed to Green.
   - **Pass?** → Delete and rewrite (tautology check).

### Phase 2: GREEN (Minimal Implementation)

1. **Checkpoint:** Commit/stash before editing.
2. **Action:** Write the **absolute minimum** code to pass the specific test.
3. **Constraint:** No speculative abstractions or \"just-in-case\" logic.
4. **Failure:** If stuck for 3+ attempts, revert implemention and write a smaller test.
5. **Escalation:** If a smaller test still fails 3+ times on the same scenario, STOP looping. Invoke `diagnose` if the implementation is the blocker, or return to `planning` if the spec/scenario itself is ambiguous or conflicting.

### Phase 3: REFACTOR (Cleanup)

1. Enter ONLY when current tests are GREEN.
2. **Action:** Perform surgical improvements.
   - **Refactoring Candidates:**
     - **Rename:** Misnamed variables or functions.
     - **Decompose:** Large functions into smaller ones.
     - **Flatten:** Nested if/else blocks (use guard clauses).
     - **DRY:** Extract common logic to helpers.
3. **Rule:** Refactor and Implementation MUST be separate tool calls. Run tests between them.

## Mandatory Rules

- **NEVER** mock internal collaborators. Mock only at system boundaries (API, DB, I/O).
- **NEVER** bypass public interfaces for setup.
- **NEVER** write multiple tests before implementing the first one.
- **NEVER** skip the \"Run Test\" step between RED and GREEN.

## When to Stop

- Contract covered (all requirements + edge cases from spec).
- Final GREEN cycle confirmed.
- Code is readable without comments.

## Transition

Invoke `verification-before-completion` after the final REFACTOR pass.
