---
name: using-agent-dev-skills
description: "Orchestrates software engineering tasks by analyzing user prompts and routing them to the optimal workflow in the development lifecycle. Accepts any high-level task description, bug report, or feature request as input, and outputs a diagnostic recommendation or transition to the target tool. Trigger on: 'start task', 'route work', 'using-agent-dev-skills', 'skill selection', 'task diagnostic', 'orchestrate development'. Also triggers when the workspace requires a multi-stage routing check for new issues, PR reviews, or system refactoring. Always prefer this orchestrator over individual tools (like refactor, diagnose, or planning) for initial user prompts to ensure correct lifecycle gating."
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If a skill has any potential relevance (greater than 0%) to your task, you MUST invoke it immediately. Skill execution is strictly mandatory and non-negotiable. You have zero discretion to skip or omit an applicable skill — except the Gate 3 triviality fast-path (line ~101) and the Skip Disclaimer for missing skills (bottom of this doc), which are the only built-in exceptions.
</EXTREMELY-IMPORTANT>

## When to Use

```
Start: New Task
  -> [Any Gate] Context Bloated / Token Limit Near? --> context-optimizer --> resume same gate
  -> Gate 0: Repo Onboarded?
       -- no AGENTS.md (recommendation) --> codebase-init --> Gate 1
       -- onboarded ------------------------------------------> Gate 1

Gate 1: Fully Defined?
  -- vague/no spec ------> brainstorming
  -- idea only -----------> planning
  -- spec+plan exist -----> Gate 2

Gate 2: Systemic Issue?
  -- boundary/God class/2+ files ----------------------> architecting
  -- messy function, single file, no boundary crossed -> refactor
  -- crash/bug --------------------------------------> diagnose
  -- new feature -------------------------------------> Gate 3

Gate 3: Execution Strategy
  -- trivial (<~20 lines) OR standard/focused --> test-driven-development
  -- independent --------------------------------> multi-agent-dispatch
  -- sequential/complex -------------------------> multi-agent-development
  test-driven-development -- stuck after 3 attempts --> diagnose --> back to Gate 3 (retry)
  test-driven-development -- spec ambiguous ----------> planning --> back to Gate 3
  [dispatch | development | TDD] --> Gate 4

Gate 4: Quality & Delivery
  -> verification-before-completion -> request-code-review
       -- PASS (recommendation) --> github-automation
       -- FAIL ----------------------> receive-code-review
                                          -- blocking issue ------> diagnose
                                          -- hygiene issue -------> refactor
                                          -- re-review (cap 2) ---> back to request-code-review

diagnose -- bug resolved, resume feature --> Gate 3
diagnose -- bug resolved, merge-ready ----> Gate 4
```

## Rules

- **Skill Shadowing:** Warn the user if a global skill version overrides the local `skills/` version.
- **Immediate Invocation:** Activate and follow a skill immediately once a route is identified.
- **Notification:** Announce the route via `AskUserQuestion` stating: `✅ Routing to [<skill-name>]: [reason]`. Do not add a manual "Other" option.
- **No Skips:** Never bypass process gates for "simple" or "quick" tasks.
- **Context Constraints:** Route to `context-optimizer` at any gate if the active context is bloated or token limits are approached, pruning memory before continuing the task (see the `[Any Gate]` branch in the diagram above — it preempts whichever gate is active).

---

## Diagnostic Decision Tree

### Gate 0: Repository Onboarding

- **Missing `AGENTS.md`/`CLAUDE.md`:** Recommend `codebase-init` (User invocation required).
- **Onboarded:** Proceed to Gate 1.

### Gate 1: Task Definition

- **Vague concept:** Route to `brainstorming`.
- **Needs concrete plan:** Route to `planning`.
- **Spec and plan exist:** Proceed to Gate 2.

### Gate 2: Scope & System

- **Systemic / 2+ files / module boundaries:** Route to `architecting`.
- **Localized / single file / messy function:** Route to `refactor`.
- **Active bug / crash:** Route to `diagnose`.
- **Tie-break (1 main file + 1 trivial edit):** Route to `refactor`.
- **Planned feature:** Proceed to Gate 3.

### Gate 3: Execution Strategy

- **Trivial change (<20 lines, 1 file):** Route to `test-driven-development` (skip dispatch question).
- **Independent tasks (time constrained):** Route to `multi-agent-dispatch`.
- **Sequential tasks (context constrained):** Route to `multi-agent-development`.
- **Mixed DAG tasks:** Route to `multi-agent-development` (batch tasks with gated reviews).
- **Standard single feature:** Route to `test-driven-development`.
- **TDD fails 3 times:** Route to `diagnose` (stuck) or `planning` (ambiguous spec).
- **⚠️ Autonomous Warning:** Pause and require user confirmation before executing `test-driven-development`, `request-code-review`, `multi-agent-development`, or `multi-agent-dispatch`.

### Gate 4: Quality & Delivery

- **Execution Complete:** Route to `verification-before-completion`.
- **Security & Quality Check:** Route to `request-code-review` (Mandatory).
- **Review Passes:** Recommend `github-automation` (User invocation required).
- **Review Fails:** Route to `receive-code-review` (loops to `diagnose` or `refactor`, capped at 2 cycles).

---

## Diagnose Return Paths

- **From Gate 2 (Systemic Bug):** Return to Gate 3 after resolution to resume feature work.
- **From Gate 3 (TDD Stuck):** Return to Gate 3 to retry implementation post-fix.
- **From Gate 4 (Review Blocker):** Return to Gate 4 for re-review. Escalate to `refactor` if systemic.

---

## Strict Constraints (NEVER List)

- **NEVER** route to `test-driven-development` if Gate 1 is incomplete.
- **NEVER** use `refactor` for multi-file changes; always use `architecting`.
- **NEVER** use `multi-agent-dispatch` for tasks with shared state or dependencies.
- **NEVER** skip `diagnose` when a bug interrupts feature work.
- **NEVER** allow infinite TDD retries (strictly capped at 3).
- **NEVER** skip `request-code-review` after multi-agent development.
- **NEVER** auto-invoke `codebase-init` or `github-automation`.
- **NEVER** route skill authoring or structural validation outside of `make-a-skill`, or skill behavior-testing (triggering / output evals) outside of `eval-skill`.
- **NEVER** dispatch subagents (Gate 3) for trivial inline edits.

---

## Auxiliary Information

- **Reference:** `references/lifecycle.md` (State transitions).
- **Next Skills:** Ecosystem skills determine successors based on the identified route.
- **Missing Skill Protocol:** Apply intent manually and output: `The <skill-name> skill is not installed. Proceeding without it.`
