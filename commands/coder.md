---
description: Spawn the coder agent to execute a coding task autonomously
argument-hint: <task description>
---

# Coder Agent Task

Delegate the following task to the coder agent: $ARGUMENTS

Full tool access (Bash, Read, Write, Edit, Glob, Grep, Skill, TodoWrite), runs in an isolated worktree. Plans with TodoWrite, executes, then verifies.

Current branch: !`git branch --show-current`
Uncommitted changes: !`git status --short`
Recent commits: !`git log --oneline -5`
Project conventions: @AGENTS.md

## Usage

- Implementing a scoped feature or fix where the approach is decided
- Refactoring a specific file or module without behavior change
- Batch changes across multiple files (renaming, reformatting, updating references)
- Running a task in isolation without polluting the main conversation context
- Follow-up after `/brainstorm` or `/plan` has produced a concrete spec

Prefer `/fix` for bugs with an error message. Prefer `/explore` when research is needed before acting.

## Execution Steps

1. Spawn Agent with `subagent_type=coder` and prompt: "$ARGUMENTS — follow AGENTS.md conventions. Use TodoWrite to plan. Run tests when done."
2. Review the diff the agent produces
3. Confirm tests pass if relevant

## Troubleshooting

**Agent returns with no changes** — Task description is too vague. Restate with a specific file, function, or behavior to change.

**Agent makes unrelated edits** — Scope the prompt: name exact files or functions in scope and add "no other changes."

**Tests fail after agent completes** — Run `/fix` with failing test output to diagnose and repair.

**Agent times out** — Break into smaller subtasks and run `/coder` on each sequentially.

## Success Criteria

- Task completed without errors
- Code follows project conventions from AGENTS.md
- Tests pass (run `npm test` if code was changed)
- Changes scoped to what was requested — no unrelated edits
