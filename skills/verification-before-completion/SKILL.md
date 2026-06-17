---
name: verification-before-completion
description: "Verify before completion. Trigger when the USER says 'looks good', 'ready to review', 'ready to merge', 'mark as done', or when Claude is about to report a task complete. Test actual behavior — not code inspection alone."
disable-model-invocation: false
---

# verification-before-completion

Guarantee operational correctness through execution evidence. **NEVER** confirm based on reading code alone.

## 0. Evidence Standards

Verification is valid ONLY when:

- **Developer Reports:** \"Tests pass, manually verified, no debug logs found.\" (Accept this).
- **Execution Proof:** Test runner output or manual interaction log (Preferred).

## 1. Mandatory Checklist

Before declaring any task done, verify ALL:

- [ ] **Targeted Tests:** Specific tests for changed code MUST pass.
- [ ] **Regression Suite:** Full test suite runs clean.
- [ ] **Manual Exercise:** If no automated tests, document inputs/outputs observed.
- [ ] **Reproduction Proof:** If fixing a bug, confirm original failure was observed, then confirm it is gone.
- [ ] **Debug Sweep:** `grep` for `console.log`, `debugger`, `print`, `pdb`.
- [ ] **Diff Audit:** Confirm every change is intentional. No accidental files staged.

## 2. Decision Logic

| Status             | Action                                                          |
| :----------------- | :-------------------------------------------------------------- |
| **CI-Only?**       | State: \"Blocked by CI. Wait for pipeline GREEN.\"              |
| **No Test Suite?** | Document changes and expected behavior. Mark as **INCOMPLETE**. |
| Regression Found?  | Stop. Invoke `diagnose`. Return here once fixed.                |
| **Complete?**      | Transition to `code-review`.                                    |

## 3. Critical Failure Modes

- **Confidence != Evidence:** \"It should work\" or \"I'm confident\" are not completion signals.
- **Green-Wash:** Tests passing but they mock away the actual logic or have no assertions.
- **Shadow Regressions:** Global state changes breaking distant, unmonitored modules.

## Transition

1. **Non-trivial changes:** Invoke `code-review`.
2. **Delivery:** Prompt user: \"Run \`/github-automation\` to submit the PR.\" (Cannot trigger automatically).

## Expert Patterns

- **N-1 Test:** Revert fix → Confirm FAIL → Re-apply fix → Confirm PASS. Eliminates \"false greens\".
- **Edge Case Blitz:** Explicitly test `null`, `undefined`, boundary integers, and empty collections.
