---
name: multi-agent-dispatch
description: "For tasks with no shared mutable state: fan out to general-purpose subagents running concurrently in one batch, then integrate their results. Trigger on 'in parallel', 'dispatch agents', 'fan out', 'multiple agents'."
disable-model-invocation: false
argument-hint: '[the independent tasks to parallelize]'
---

# multi-agent-dispatch

Maximize efficiency through parallel execution across isolated problem domains.

## Dispatch Gate

Answer BOTH before spawning:

1. **Authorized?** User requested parallel/agent work OR parent skill phase calls for it.
2. **Independent?** 2+ domains with NO shared mutable state (disjoint files/hypotheses).
   → If NO to either: Investigate inline or sequentially.

## The Four-Step Loop

1. **GROUP:** Split work into independent domains. One agent per domain. Name what is OUT of scope.
2. **SELECT:** Configure `general-purpose` agents with specialized roles in prompt constraints.
   - **Investigator (Read-only):** Trace root cause, provide fix as code block. No edits.
   - **Writer (Isolation: worktree):** Implement spec, write tests, report changes.
   - **Researcher (Read-only):** Explore code/docs, report file paths and usages.
3. **LAUNCH:** Before launching, enumerate each subagent's intended write-paths (from its SCOPE) and diff them against every other subagent's write-paths. If any overlap is found, fail closed: do NOT launch in parallel — defer to `multi-agent-development` instead. Only if disjoint, emit ALL `Agent` calls in **ONE message** for true concurrency.
4. **INTEGRATE:** Reconcile findings/diffs. Run full project validation.

## Subagent Prompt Contract (Zero-Shot)

Every prompt MUST contain:

- **SCOPE:** Validated paths (In/Out of bounds).
- **OBJECTIVE:** One concrete verifiable/falsifiable outcome.
- **CONTEXT:** Error text, versions, baseline commit — everything to start cold.
- **CONSTRAINTS:** Tool restrictions and specific "Do Not" rules.
- **OUTPUT:** Exact final message schema (the only artifact returned).

## Integration Rules

- **Reads are free.** Writes MUST be disjoint to avoid stomping.
- **No shared history.** Subagents start cold; embed every fact verbatim.
- **Validate Claims.** Never trust a report without running the test suite.

## Success Criteria

All results reconciled, test suite GREEN, handed to `verification-before-completion`.
