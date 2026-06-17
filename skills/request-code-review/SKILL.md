---
name: request-code-review
description: "Mandatory quality gate before delivery. Trigger on 'code review', 'review this diff', 'any issues with this', 'check for bugs', 'quality review'. ALSO trigger automatically: (1) after verification-before-completion confirms tests pass, (2) before opening a PR/shipping the change, (3) on any non-trivial change that will be committed. Do not skip — correctness bugs and security issues discovered here are cheaper to fix than after merge."
disable-model-invocation: false
argument-hint: '[target: branch, commit, file, or "current diff"]'
allowed-tools: Bash(git *), Agent
disallowed-tools: Write, Edit
---

# request-code-review

Get an unbiased review by dispatching a fresh-context subagent — never review your own work in the same thread that wrote it.

## Step 0: Confirm

This will start an autonomous session (~N calls). Proceed? Wait for explicit user confirmation before scanning.

## Pre-Review Checkpoint

1. **Verification:** Confirm unit tests passed (`verification-before-completion`).
2. **Gather context:** Get the commit range (`git log --oneline -10` if unsure which commit started this work) and a one-paragraph summary of what was supposed to be built (from the plan/spec if one exists, otherwise from the user's original request).

## Why a fresh subagent

The agent that wrote the code is biased toward believing it's correct — it already rationalized every decision once. A subagent with zero memory of the implementation will read the diff cold, the same way a human reviewer would. This matters most after `multi-agent-development`/`multi-agent-dispatch` work, but applies even to single-thread changes.

## Phase 1: Dispatch

1. **Stat Check:** `git diff --stat {{base}}..{{head}}` to confirm the range is what you expect before dispatching.
2. **Build the prompt:** Fill in `references/reviewer-dispatch-prompt.md` with the base commit, head commit, repo path, and the requirements summary. Point it at `references/patterns.md` for the pattern catalog.
3. **Dispatch:** `Agent(subagent_type: general-purpose, description: "Code review of <range>", prompt: <filled template>)`. Do not run the scan yourself — the subagent does the reading and judging.
4. **No git, no diff:** If there's nothing to diff against (e.g. uncommitted scratch work), request `Before/After` blocks for each file and review inline instead of dispatching — a subagent can't read code that isn't on disk or in git.

## Phase 2: Receive the Result

Take the subagent's `## Code Review Result` output verbatim — do not edit, soften, or re-summarize its findings before deciding what to do with them. Hand it directly to `receive-code-review` for processing (verification, pushback, and implementation order are that skill's job, not this one's).

## Transition

1. **PASS:** Prompt user: "Run `/github-automation` to open the PR."
2. **FAIL (any blocking tier):** Invoke `receive-code-review` with the full result. Do not start fixing things directly from this skill.

## NEVER

- Never review your own diff in the same thread you wrote it in — dispatch a subagent.
- Never let the dispatched subagent edit files; it is read-only.
- Never accept "looks good" without a stated `## Code Review Result` block.
- Never review in isolation; always require a diff or explicit before/after blocks.
