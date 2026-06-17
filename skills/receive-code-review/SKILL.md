---
name: receive-code-review
description: "How to process code review feedback once you have it — from request-code-review's dispatched subagent, a human partner, or an external GitHub reviewer/bot. Trigger on 'review feedback', 'reviewer said', 'PR comments', 'fix these review comments', or immediately after request-code-review returns a FAIL result. Governs verification before implementing and pushback when feedback is wrong — not how to produce a review."
disable-model-invocation: false
---

# receive-code-review

Code review feedback requires technical evaluation, not emotional performance or blind compliance. Verify before implementing. Ask before assuming.

## 0. Identify the Source

- **From `request-code-review`'s dispatched subagent:** Treat like an external reviewer below — it had zero conversational context, so verify its findings against the actual codebase before acting; it can be wrong about intent it never saw.
- **From the user (your human partner) directly:** Trusted — implement after understanding. Still ask if scope is unclear. No performative agreement.
- **From an external GitHub reviewer/bot/PR comment:** Most scrutiny required — see Phase 2.

## 1. Read Before Reacting

1. **Read the complete feedback** — every item — before responding to any of it.
2. **If any item is unclear, STOP.** Do not implement the items you do understand while asking about the rest; items may be related and partial understanding produces a wrong implementation. Ask for clarification on all unclear items at once.

## 2. Verify (mandatory before implementing)

For each finding, before touching code:

- [ ] Is this technically correct for **this** codebase (not a generic best practice)?
- [ ] Does the suggested fix break existing functionality or tests?
- [ ] Is there a reason the current implementation looks this way (legacy, platform constraint, prior decision)?
- [ ] Does the reviewer's suggestion conflict with a decision the user already made in this conversation or in `CLAUDE.md`/`AGENTS.md`? If so, stop and raise it with the user — do not silently override either side.
- [ ] **YAGNI check** for "implement this properly" suggestions: `git grep` for actual usage. If unused, ask whether to remove it (YAGNI) instead of building it out.

If you can't verify a finding without more information, say so explicitly and ask how to proceed — don't implement a guess.

## 3. Respond

**Forbidden:** "You're absolutely right!", "Great point!", "Excellent feedback!", any gratitude expression, "Let me implement that now" before verification.

**Use instead:**

- Correct and verified: state the fix factually — `"Fixed. [what changed]"` or just make the change and let the diff speak.
- Wrong, with evidence: push back with technical reasoning, cite the specific file/test/constraint that contradicts the suggestion.
- Can't verify: state the limitation and ask — `"Can't verify this without [X]. Should I [investigate/ask/proceed]?"`
- You pushed back earlier and were wrong: `"Checked [X] — it does [Y]. Fixing."` State the correction and move on, no apology spiral.

## 4. Implement in Severity Order

1. Blocking issues first (Tier 1 security, Tier 2 correctness from `request-code-review`'s rubric, or equivalent "must fix" items from a human/external reviewer).
2. Simple fixes (typos, imports).
3. Complex fixes (refactoring, logic changes).
4. Test each fix individually — do not batch several fixes and run tests once at the end.

## Routing Blocking Issues

- **Tier 1 / Tier 2 (security or correctness):** Invoke `diagnose` to root-cause the issue properly rather than patching the symptom.
- **Tier 4 (reuse/hygiene) or structural feedback:** Invoke `refactor`.
- After the fix lands, return to `verification-before-completion`, then back to `request-code-review` for re-review of the same range.

## GitHub Thread Replies

When replying to inline PR review comments, reply in the comment thread (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), not as a top-level PR comment — keeps the conversation attached to the actual line being discussed.

## NEVER

- Never write a performative-agreement phrase ("you're absolutely right", "great catch") — the fix itself is the acknowledgment.
- Never implement a finding you haven't verified against this codebase, even from a trusted source.
- Never batch-implement several items then test once — one fix, one test, repeat.
- Never silently accept a suggestion that contradicts a decision the user already made — surface the conflict instead.
