---
name: multi-agent-dispatch
description: "Parallel execution for independent tasks. Fans out to isolated subagents for efficiency. Not for tasks with shared mutable state or dependencies — those need strict ordering (see multi-agent-development). Trigger on: 'in parallel', 'dispatch agents', 'fan out', 'multi-agent-dispatch', 'independent tasks', 'concurrent execution'."
disable-model-invocation: false
argument-hint: '[the independent tasks to parallelize]'
---

# multi-agent-dispatch

Maximize efficiency through parallel execution across isolated problem domains. Independent domains (no shared state) → this skill. Shared mutable state or dependencies → `multi-agent-development` instead; see Dispatch Gate below for the exact test.

```
GROUP -> SELECT -> LAUNCH -> INTEGRATE
                      ^         |
                      └─ retry ─┘ (partial failure)
```

## NEVER Do This

- **NEVER** launch parallel subagents if their write-paths overlap. **WHY:** This causes race conditions and git conflicts. **FIX:** Use `multi-agent-development` for sequential execution.
- **NEVER** assume a subagent has context from the parent thread. **WHY:** Subagents start cold. **FIX:** Embed every necessary fact verbatim in the prompt.
- **NEVER** launch more than 3 subagents in a single batch. **WHY:** Each subagent's full report lands in the main thread's context — at 4+ concurrent, the integration step alone can blow the budget before you've reconciled a single finding. **FIX:** Batch in waves of ≤3; integrate each wave before launching the next.
- **NEVER** accept subagent reports as final truth. **WHY:** Subagents can hallucinate success. **FIX:** You MUST run the project's test suite to verify all claims.

## Dispatch Gate

Answer BOTH before spawning:

1. **Authorized?** User requested parallel/agent work OR parent skill phase calls for it.
2. **Independent?** 2+ domains with NO shared mutable state (disjoint files/hypotheses) AND no hidden coupling. Disjoint write-paths alone are not sufficient — also check:
   - Does any agent's correctness _assume_ another agent already ran (an ordering assumption), even if it never writes to that agent's files?
   - Do two or more agents read-then-act on the same external resource (a shared branch/PR, a rate-limited API budget, a singleton config/lockfile, a shared DB row) where one agent's action invalidates another's assumption?
   - Would the result differ if the agents ran in a different order or interleaving? If yes, they are not independent.
     → If NO to authorization, OR if disjoint files but hidden coupling exists, OR if both are unclear: Investigate inline or use `multi-agent-development` instead.

## The Four-Step Loop

**MANDATORY — before Step 2 (SELECT):** Read [`references/subagent-contract.md`](references/subagent-contract.md) in full. It defines the SCOPE/OBJECTIVE/CONTEXT/CONSTRAINTS/OUTPUT SCHEMA contract and the Investigator/Writer/Researcher role vocabulary used below. Do not configure or launch any agent before reading it.

1. **GROUP:** Analyze the work and confirm the parallel grouping via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually:
   - ✅ **Recommended** — [Groups] based on [disjoint files/hypotheses].
   - **Alternative** — [Alternative Grouping] + justification for the different split.
2. **SELECT:** Configure `general-purpose` agents with specialized roles per the Role Vocabulary in `subagent-contract.md` (Investigator/Writer/Researcher). For read-only roles, explicitly instruct no Write/Edit — and note this is an instruction, not an enforced restriction, unless the harness supports a tool allowlist. **Writer roles MUST be launched with `isolation: worktree`** — this is the actual mechanism that makes "writes MUST be disjoint" true; without it, two Writers editing the same working tree can stomp each other even with disjoint SCOPE.
3. **LAUNCH:**
   - Enumerate each subagent's intended write-paths (from its SCOPE).
   - Diff them against every other subagent's write-paths.
   - **Limit:** Max 3 concurrent agents per batch.
   - If disjoint, emit ALL `Agent` calls in **ONE message** for true concurrency.
4. **INTEGRATE:** Reconcile findings/diffs. Run full project validation.

**Partial-failure protocol (INTEGRATE step):** if some agents in a batch return `SUCCESS` and others return `BLOCKED`/crash/timeout:

- Keep the successful, validated results — do not discard or re-run agents that already succeeded and passed validation.
- Re-dispatch only the failed domains, with a fresh agent and the same SCOPE (do not reuse a failed agent's context).
- If a failed domain blocks on something a successful domain's result would resolve (rare, since domains are supposed to be disjoint — if this happens, the Dispatch Gate's independence check above was wrong), stop and re-classify as sequential via `multi-agent-development` instead of forcing a re-dispatch.
- Never silently mark the batch "done" with a known BLOCKED domain unreported — surface partial completion to the user explicitly.

**next skills:**

- `verification-before-completion`: Once all parallel tasks are integrated, to verify the final combined state against project standards.
- `multi-agent-development`: If the partial-failure protocol reveals hidden coupling between "independent" domains — re-classify as sequential rather than forcing another dispatch.
- `diagnose`: If integration reveals a regression or conflict between two agents' changes that needs root-cause analysis rather than a guessed merge.

## Integration Rules

- **Reads are free.** Writes MUST be disjoint (see Step 2/SELECT above).
- **Validate Claims.** Never trust a report without running the test suite.

## Success Criteria

All results reconciled, test suite GREEN, handed to `verification-before-completion`.
