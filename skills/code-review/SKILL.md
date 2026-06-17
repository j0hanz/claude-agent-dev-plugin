---
name: code-review
description: "Mandatory quality gate before delivery. Trigger on 'code review', 'review this diff', 'any issues with this', 'check for bugs', 'quality review'. ALSO trigger automatically: (1) after verification-before-completion confirms tests pass, (2) before opening a PR/shipping the change, (3) on any non-trivial change that will be committed. Do not skip — correctness bugs and security issues discovered here are cheaper to fix than after merge."
disable-model-invocation: false
argument-hint: '[target: branch, commit, file, or "current diff"]'
allowed-tools: Bash(git *)
disallowed-tools: Write, Edit
---

# code-review

Focused scan for correctness, security, and hygiene regressions.

## Step 0: Confirm

This will start an autonomous session (~N calls). Proceed? Wait for explicit user confirmation before scanning.

## Pre-Review Checkpoint

1. **Verification:** Confirm unit tests passed (`verification-before-completion`).
2. **Context:** Run `/compact` or `/clear` to remove conversational noise before scanning.

## Phase 1: The Diff

1. **Stat Check:** `git diff --stat origin/main..HEAD`
2. **Deep Scan:** `git diff origin/main..HEAD` (or target specified).
3. **Manual Check:** If no git, request `Before/After` blocks for each file.

## Phase 2: Risk-Ordered Scan (Tiered)

Scan in strict priority order. Stop and block on any Tier 1.

### Tier 1: Security (Blocking)

- **Injection:** Shell/exec args, SQL concatenation, Path traversal.
- **Secrets:** Hardcoded keys, tokens, or credentials in code/logs.
- **Auth/Authz:** Permission checks before actions; session handling.
- **Input:** Unsafe deserialization (pickles, yaml.load, JSON.parse).

### Tier 2: Correctness (Blocking)

- **Logic:** Off-by-one, boolean errors, logic inversions, async/await gaps.
- **Safety:** Null/undefined dereferences, unhandled edge cases.
- **Errors:** Swallowed/empty catch blocks; missing log context.

### Tier 3: Performance (Advisory)

- **Regressions:** New N+1 queries, unbounded loops, or large copies in hot paths.
- **Resource:** Missing depth limits on recursion/retries.

### Tier 4: Reuse & Hygiene (Advisory)

- **Reuse:** `git grep` for existing utilities before accepting new helpers.
- **Hygiene:** Breaking API changes, confusing public names, missing docs.

## Phase 3: Review Result (Mandatory Output)

```markdown
## Code Review Result

**Status**: [PASS ✓ | FAIL ✗ (N blocking)]

### Blocking Issues

- [file:line] [Type] — [Issue] → [Required Fix]

### Advisory Issues

- [file:line] [Type] — [Observation] → [Recommendation]

### What Was Checked

- Tier 1 (Security): [concise summary]
- Tier 2 (Correctness): [concise summary]
- Tier 3 (Performance): [concise summary]
- Tier 4 (Reuse/API): [concise summary]
```

## FAIL Transition

- **Tier 1 / Tier 2 (Blocking, Security or Correctness):** Invoke `diagnose` to root-cause the issue.
- **Tier 4 (Blocking, Reuse/Hygiene):** Invoke `refactor` to restructure.
- After the fix lands, re-enter `verification-before-completion` before returning here for re-review.

## Transition

1. **PASS:** Prompt user: "Run `/github-automation` to open the PR."
2. **FAIL:** Follow the FAIL Transition above, then re-review once fixed.

## NEVER

- Never accept "looks good" without stating what was checked.
- Never review in isolation; always require a diff.
- Never conflate advisory (style) and blocking (correctness) issues.
