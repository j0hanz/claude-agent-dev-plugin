---
description: Run structured requirements discovery before implementing a feature or change
argument-hint: <feature or change description>
---

# Brainstorming

Run a brainstorming session for: $ARGUMENTS

Use this before any non-trivial implementation to surface design gaps, ambiguous terminology, and misaligned assumptions. The brainstorming skill asks clarifying questions, maps out the design space, and produces a requirements summary that informs the next /plan or /coder invocation. Prevents rework.

Current skills: !`ls skills/`
Current agents: !`ls agents/`
Project config: @AGENTS.md

## When to Use

- Starting a new feature and the scope or approach isn't fully clear
- Domain terminology is ambiguous (e.g., "task", "session", "context" could mean different things)
- Multiple implementation approaches exist and you want to pick the right one before writing code
- A stakeholder description is vague and needs to be turned into concrete requirements
- You want to catch design problems before `/plan` or `/coder` starts executing

Prefer `/plan` when requirements are already clear and you need an execution strategy. Prefer `/coder` when both requirements and approach are decided.

## Execution Steps

1. Invoke the brainstorming skill: `Skill("brainstorming", "$ARGUMENTS")`
2. Answer any clarifying questions the skill surfaces
3. Review the requirements summary and design decisions
4. When done, optionally follow up with /plan to build an implementation plan

## Troubleshooting

**Skill returns immediately with no questions** — The input may be too narrow. Add more context about the feature goal and rerun.

**Requirements feel incomplete** — Push back in the conversation: ask the skill to explore edge cases, failure modes, or the "what should NOT happen" space.

**Brainstorm diverges from what you actually want** — Provide a constraint upfront (e.g., "only changes within the hook layer, no new agents").

**Skill not found error** — Run `ls skills/` to confirm the brainstorming skill is installed, then retry.

## Success Criteria

- All ambiguous terms defined
- Scope boundaries clear (what's in, what's out)
- Key design decisions documented with rationale
- Ready to hand off to /plan or /coder without open questions

Catch design problems here — not after code has been written.
