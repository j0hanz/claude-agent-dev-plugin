---
description: Spawn the explorer agent to research a question about the codebase or documentation
argument-hint: <research question>
---

# Explorer Agent Research

Delegate this research question to the explorer agent: $ARGUMENTS

Read-only (no writes). Has access to Glob, Grep, Read, WebSearch, WebFetch, and Context7 for live library docs. Returns a structured report.

Project config: @AGENTS.md
Agents: !`ls agents/`
Skills: !`ls skills/`

## Usage

- "Where is X defined?" or "which files reference Y?"
- Researching a library, framework, or API before writing code
- Understanding an unfamiliar area before making changes
- Gathering context before `/fix` or `/coder`
- Validating: "does this project already have a helper for X?"

Prefer `/fix` when the problem is known. Prefer `/coder` when research is done and the task is clear.

## Execution Steps

1. Spawn Agent with `subagent_type=explorer` and prompt: "Research: $ARGUMENTS — Search the project codebase and skills directory. Fetch live docs via Context7 if relevant. Return a structured, concise report with file paths and line references."
2. Relay findings to the conversation
3. Follow up with `/coder` or `/fix` based on findings

## Troubleshooting

**Explorer returns nothing useful** — Rephrase with specific terms (function names, file patterns, exact error messages).

**Live docs are stale or wrong** — Context7 may not match the installed version. Ask the explorer to check local lock files for the pinned version.

**Explorer searches the wrong directory** — Searches project root by default. Name the specific subdirectory explicitly.

**Report is too broad** — Scope it: "Only search hooks/ and skills/, return at most 5 files."

## Success Criteria

- Question answered with specific file paths and line references
- External docs fetched and cited if relevant
- Findings are actionable — not raw search output
