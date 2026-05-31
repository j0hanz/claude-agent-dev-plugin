---
description: Spawn the coder agent to execute a coding task autonomously
argument-hint: <task description>
---

# Coder Agent Task

Delegate the following task to the coder agent: $ARGUMENTS

The coder agent has full tool access (Bash, Read, Write, Edit, Glob, Grep, Skill, TodoWrite) and runs in an isolated worktree. Use it for feature implementation, bug fixes, refactoring, and batch code changes. It plans with TodoWrite, executes, then verifies.

Current branch: !`git branch --show-current`
Uncommitted changes: !`git status --short`
Recent commits: !`git log --oneline -5`
Project conventions: @AGENTS.md

## When to Use

- Implementing a clearly scoped feature or fix where the approach is already decided
- Refactoring a specific file or module without changing behavior
- Batch changes across multiple files (renaming, reformatting, updating references)
- Running a task in isolation without polluting the main conversation context
- Follow-up after `/brainstorm` or `/plan` has produced a concrete spec

Prefer `/fix` when you have a specific bug with an error message. Prefer `/explore` when you need research before acting.

## Execution Steps

1. Spawn Agent with subagent_type=coder and this prompt: "$ARGUMENTS — follow AGENTS.md conventions. Use TodoWrite to plan. Run tests when done."
2. Review the diff output the agent produces
3. If tests are relevant, confirm they pass

## Troubleshooting

**Agent returns with no changes** — The task description may be too vague. Restate it with a specific file, function, or behavior to change.

**Agent makes unrelated edits** — Scope the prompt more tightly: name the exact files or functions in scope and add "no other changes."

**Tests fail after agent completes** — Run `/fix` with the failing test output as input to diagnose and repair.

**Agent times out mid-task** — Break the task into smaller subtasks and run `/coder` on each sequentially.

## Success Criteria

- Task completed without errors
- Code follows project conventions from AGENTS.md
- Tests pass (run `npm test` if code was changed)
- Changes scoped to what was requested — no unrelated edits

The coder agent handles the execution; you handle the review.
