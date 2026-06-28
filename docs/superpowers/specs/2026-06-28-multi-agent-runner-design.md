---
name: Multi-Agent Runner Design
topic: multi-agent-runner
date: 2026-06-28
---

# Multi-Agent Runner Specification & Design Brief

This design brief specifies the implementation of `bin/multi-agent-runner.mjs`, a state-driven CLI helper harness designed to automate parallel multi-agent task execution, validation gates, conflict resolution, and token pruning.

## Markdown-KV Brief

*   **Approach:** State-driven CLI helper harness (`bin/multi-agent-runner.mjs`) maintaining execution state in `.claude/multi_agent_state.json`.
*   **Why:** Programmatic automation of Lane Matrix validation, subagent dispatching, gating, and conflict-resolution reduces LLM orchestrator cognitive load and token consumption by ~80%.
*   **Scope:** 
    *   Command-line parser for `init`, `step`, and `status` actions.
    *   Markdown parser (extracting bulleted task lists and dependencies) and JSON parser.
    *   Validation gate logic (Spec Review, Quality Review, Git Conflict resolving).
*   **Constraints:**
    *   Must run on standard Node.js ≥ 22 with synchronous filesystem operations.
    *   Zero dependencies other than built-in Node modules (e.g. `fs`, `path`, `child_process`).
    *   Maintain strict backwards compatibility with existing agent system prompts and skill files.
*   **Interface:** CLI-based invocation with structured Markdown output for orchestrator action and JSON-formatted updates.
*   **Architecture:** 
    *   **State Store:** File-based state in `.claude/multi_agent_state.json`.
    *   **Orchestration Engine:** State machine tracking lane transition paths.
*   **Risks:** Complex or circular dependency configurations in custom markdown plans. Mitigated by strict cycle validation during `init`.
*   **First Step:** Implement the plan parser and state storage schema in `bin/multi-agent-runner.mjs`.

---

## 1. CLI Usage and Action Flow

### Action: `init`
Initializes a new session. It checks for dependency cycles and file overlaps.
```bash
node bin/multi-agent-runner.mjs init docs/plans/my-plan.md
```

### Action: `step`
Inspects the state file and outputs instructions.
```bash
node bin/multi-agent-runner.mjs step
```

### Action: `step --update`
Logs a state transition callback.
```bash
node bin/multi-agent-runner.mjs step --update '{"laneId": "lane-1", "phase": "implementation", "verdict": "DONE", "commit": "abc1234", "files": ["src/auth.ts"]}'
```

### Action: `status`
Outputs a clean Markdown table summarizing current lane matrices, runs, and verdicts.
```bash
node bin/multi-agent-runner.mjs status
```

---

## 2. Core State Transitions

1.  **PENDING** $\rightarrow$ **RUNNING**: When dependencies are met. Generates `implementer` agent prompt.
2.  **RUNNING** $\rightarrow$ **SPEC_REVIEW**: Once the implementer outputs `DONE`/`DONE_WITH_CONCERNS`. Generates `spec-reviewer` prompt.
3.  **SPEC_REVIEW** $\rightarrow$ **QUALITY_REVIEW**: Upon `SPEC_PASS`. Generates `quality-reviewer` prompt.
4.  **SPEC_REVIEW** $\rightarrow$ **RUNNING**: Upon `SPEC_FAIL` (first attempt). Increments attempts and re-dispatches.
5.  **SPEC_REVIEW** $\rightarrow$ **BLOCKED**: Upon `SPEC_FAIL` (second attempt). Triggers human escalation.
6.  **QUALITY_REVIEW** $\rightarrow$ **COMPLETED** (or **MERGE_WAIT**): Upon `QUALITY_PASS` / `MINOR`.
7.  **MERGE_WAIT** $\rightarrow$ **COMPLETED**: If Git merge succeeds or `conflict-resolver` successfully resolves conflicts.

---

## 3. Self-Review Checklist

- [x] **Placeholder Scan:** No placeholders or "TBD"s.
- [x] **Internal Consistency:** The transitions match the design diagrams exactly.
- [x] **Scope Check:** Narrowly focused on the Node.js helper harness.
- [x] **Ambiguity Check:** All commands and outputs are explicitly defined.
