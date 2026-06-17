---
name: multi-agent-development
description: "For tasks with dependencies between them: execute a multi-task plan one task at a time, delegating each to a focused general-purpose implementer subagent and running two review gates (spec compliance, then code quality) before advancing. Trigger on 'implement the plan', 'execute spec', 'agentic development'."
disable-model-invocation: false
argument-hint: '[path to plan file]'
---

# multi-agent-development

Orchestrate sequential task execution with zero context pollution and high quality-assurance.

## Decision Gate

- **Dependencies or shared state?** → **Sequential** (This skill).
- **Independent tasks?** → **Parallel** (`multi-agent-dispatch`).

## The Core Loop (Per Task)

Execute Phases 1 → 2 → 3 in strict order.

### Phase 1: Implement

- Dispatch a `general-purpose` subagent with `isolation: \"worktree\"`.
- **Prompt Contract:** Carry `SCOPE`, `OBJECTIVE`, `CONTEXT`, `CONSTRAINTS`.
- **Outcome:** `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`.

### Phase 2: Spec Compliance Gate

- Dispatch a read-only `general-purpose` agent as Reviewer (`references/spec-reviewer-prompt.md`).
- **Check:** Did implementer build everything? Anything extra?
- **Failure:** Dispatch implementer to fix. Max 2 attempts before escalating as BLOCKED.

### Phase 3: Code Quality Gate

- Dispatch a read-only `general-purpose` agent as Quality Auditor (`references/quality-reviewer-prompt.md`).
- **Check:** Responsibility, decomposition, error handling, test coverage.
- **Severity:** `CRITICAL` (Block), `IMPORTANT` (Block), `MINOR` (Log).

## Final Validation

Advance only after Phase 3 passes. After ALL tasks pass:

1. `npm test && npm run validate`
2. Invoke `verification-before-completion`

## Operational Rules

- **NEVER** skip Phase 2 or 3 to save time.
- **NEVER** trust a summary. Verify actual code.
- **NEVER** reuse subagents across tasks. Fresh agent per task.
- **NEVER** start implementation without verifying disjoint file sets.
- **Prompt Discipline:** Subagents start cold. Embed every fact.
