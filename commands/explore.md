---
description: Spawn the explorer agent to research a question about the codebase or documentation
argument-hint: <research question>
---

# Explorer Agent Research

Delegate this research question to the explorer agent: $ARGUMENTS

The explorer agent is read-only (no writes) and has access to Glob, Grep, Read, WebSearch, WebFetch, and Context7 for live library docs. Use it for codebase exploration, symbol lookups, architecture questions, and external API/library research. It returns a structured report.

Project config: @AGENTS.md
Agents: !`ls agents/`
Skills: !`ls skills/`

## When to Use

- Answering "where is X defined?" or "which files reference Y?" across the codebase
- Researching a library, framework, or API before writing code that uses it
- Understanding the architecture of an unfamiliar area before making changes
- Gathering context before opening a `/fix` or `/coder` task
- Validating an assumption ("does this project already have a helper for X?")

Prefer `/fix` when you already know what's broken. Prefer `/coder` when the research phase is done and the task is clear.

## Execution Steps

1. Spawn Agent with subagent_type=explorer and prompt: "Research: $ARGUMENTS — Search the project codebase and skills directory. Fetch live docs via Context7 if relevant. Return a structured, concise report with file paths and line references."
2. Relay the findings to the conversation
3. If further action is needed, use /coder or /fix based on findings

## Troubleshooting

**Explorer returns nothing useful** — Rephrase the question with more specific terms (function names, file patterns, or exact error messages).

**Live docs are stale or wrong** — Context7 fetches current docs but may not match the exact installed version. Ask the explorer to also check local lock files for the pinned version.

**Explorer searches the wrong directory** — The agent searches the project root by default. If the target is in a specific subdirectory, name it explicitly in the question.

**Report is too broad** — Scope it: "Only search hooks/ and skills/, return at most 5 files."

## Success Criteria

- Question answered with specific file paths and line references
- External docs fetched and cited if relevant
- Findings are actionable — not just raw search output

Research first, act second — explorer saves you from fixing the wrong thing.
