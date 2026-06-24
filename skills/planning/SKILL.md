---
name: planning
description: 'Generates specs.md and plan.md files from a feature description. Use when the user requests "write a spec", "create implementation plan", "spec and plan this", "production rollout plan", or "task decomposition". Action: produces ordered checklists and architectural guidelines.'
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *)
argument-hint: '[--depth sketch|contract|blueprint] [--spec-only] [--from-spec <file>] [--domain api|cli] <feature description>'
---

# planning

Paired `plan/NAME.specs.md` (What/Why/Acceptance) and `plan/NAME.plan.md` (Atomic/Ordered tasks).

## Process Flow

```
Step 1: Intake & Mapping (brief/interview) -> Step 2: Artifact Authoring (scaffold/draft) -> Step 3: Validation Pipeline
  -- errors found ----------> back to Step 2
  -- depth == sketch -------> Step 5: Handoff
  -- depth > sketch --------> Step 4: Semantic Review
                                 -- approved ---> Step 5: Handoff
                                 -- not ready ---> back to Step 2
```

## Constraints & Safety

- **Bash Execution:** Enclose user variables in single quotes to prevent injection in `Validate:` commands.
- **Paths & Spec IDs:** Execute `scripts/scaffold.py`/`scripts/discover.py`. **NEVER** hand-type to avoid dead links.
- **Validation Gates:** Mandate 100% PASS before proceeding. **NEVER** bypass.
- **Field Modification:** Execute `scripts/sync.py` to map `Satisfies:` in Contract/Blueprint. **NEVER** edit manually.
- **Prerequisites:** Read templates and decomposition guide prior to drafting.
- **Subagent Safety:** Wrap untrusted user context inside `<untrusted_context>` tags.

## Depth Profiles

- **`sketch`:** Goal + REQs + Rough Interfaces | Compact Phases | Scope: _Rough ideas / unknown_.
- **`contract`:** 8 Sections + Interface Errors | Atomic Tasks | Scope: _Known goal / interface (Default)_.
- **`blueprint`:** Contract + Rollback + Mermaid | Narrative Runbook | Scope: _Prod rollout / migration_.

## Step 1: Intake & Mapping

- **Mandatory Read:** `references/discovery.md` (for path resolution).
- **Prohibited Read:** `references/validation.md`, `references/traceability.md`, `references/spec-template.md`, `references/plan-template.md`.
- **Brief Mapping:** Auto-map provided Design Brief (Brief Why → Rationale, Brief Chosen Approach → Goal, etc.). Skip asking mapped fields.
- **Missing Data Queries:** Batch questions via `AskUserQuestion` (max 4 per call). Query **ONLY** missing Goal (1 sentence) and Interfaces (I/O). Mark others `UNKNOWN: [reason]`.
- **Query Format:** Require 1 `✅ Recommended` [Value] and 1 `Alternative` [Option + context]. Auto-supplied "Other" applies.

## Step 2: Artifact Authoring

- **Mandatory Read:** `references/spec-template.md`, `references/plan-template.md`, `references/decomposition.md`, `references/traceability.md`, `references/output-examples.md`, `references/domain-examples.md`.
- **Scaffold Action:** `python skills/planning/scripts/scaffold.py <name> --depth [sketch|contract|blueprint]`
- **Spec Draft:** Complete requirements and interfaces strictly via `references/spec-template.md`.
- **Plan Draft:** Break down into atomic tasks via `references/decomposition.md`. Fetch existing paths via `scripts/discover.py`. Prefix non-existent paths with `[UNVERIFIED]`.

## Step 3: Validation Pipeline

- **Mandatory Read:** `references/validation.md`.
- **Prohibited Read:** `references/discovery.md`, Templates.
- **Gate:** Resolve all ERRORS (100% pass required). Omitted depth defaults to `contract`.
- **Sketch Command:** `python skills/planning/scripts/validate.py <name> --spec --level sketch` _(No sync phase)._
- **Contract/Blueprint Command:** `python skills/planning/scripts/execute_plan_pipeline.py --name <name> --depth [contract|blueprint]` _(Pipeline: spec-validation → scripts/sync.py → plan-validation → cross-validation)._

## Step 4: Semantic Review (Contract/Blueprint)

- **Subagent Dispatch:** Utilize `general-purpose` agent to audit quality.
- **Contract Rule:** Enforce prompt structure via `../multi-agent-development/references/subagent-contract.md`.
- **Payload Input:** Provide `references/validation.md` + `scripts/validate.py` output.
- **Payload Output:** Write to `plan/NAME.review.md`.
- **Execution Gate:** Block handoff until review outputs `ready_for_execution: true`.
- **Review Verify:** `python skills/planning/scripts/validate.py <name> --review`

## Step 5: Handoff

- **Commit Baseline:** Mandate committed state. Append output of `git rev-parse HEAD` to handoff message for `multi-agent` tasks (diffing fails without it).
- **Target `test-driven-development`:** Single focused feature/fix.
- **Target `multi-agent-development`:** Sequential multi-task execution with gated reviews.
- **Target `multi-agent-dispatch`:** Parallel independent task clusters.
- **Target `context-optimizer`:** If context bloats during Step 1/2's mandatory reference reads, before continuing.

## Canonical Task Block Schema

```markdown
### TASK-NNN: [Action title]

Depends on: [TASK-NNN](#anchor) or none
Files: [path/to/file.ts](path/to/file.ts)
Symbols: [symbolName](path/to/file.ts#L42)
Satisfies: REQ-001, SEC-002
Action: Single specific imperative implementation action.
Validate: `[runnable shell command]`
Expected result: Observable success signal.
```
