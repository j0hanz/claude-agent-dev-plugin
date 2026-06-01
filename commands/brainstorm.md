---
description: Run structured requirements discovery before implementing a feature or change
argument-hint: <feature or change description>
---

# Brainstorming

Run a brainstorming session for: $ARGUMENTS

Surfaces design gaps, ambiguous terminology, and misaligned assumptions before implementation. Asks clarifying questions, maps the design space, and produces a requirements summary for `/plan` or `/coder`.

Current skills: !`ls skills/`
Current agents: !`ls agents/`
Project config: @AGENTS.md

## Usage

- Scope or approach is unclear before starting a feature
- Domain terminology is ambiguous ("task", "session", "context")
- Multiple implementation approaches exist and the right one isn't decided
- A stakeholder description needs to become concrete requirements

Prefer `/plan` when requirements are clear. Prefer `/coder` when requirements and approach are both decided.

## Execution Steps

1. Invoke the brainstorming skill: `Skill("brainstorming", "$ARGUMENTS")`
2. Answer clarifying questions the skill surfaces
3. Review the requirements summary and design decisions
4. Follow up with `/plan` to build an implementation plan

## Troubleshooting

**Skill returns with no questions** — Input is too narrow. Add context about the feature goal and rerun.

**Requirements feel incomplete** — Ask the skill to explore edge cases, failure modes, or "what should NOT happen."

**Brainstorm diverges from goal** — Add a constraint upfront (e.g., "only changes within the hook layer, no new agents").

**Skill not found** — Run `ls skills/` to confirm installation, then retry.

## Success Criteria

- All ambiguous terms defined
- Scope boundaries clear (in-scope and out-of-scope)
- Key design decisions documented with rationale
- No open questions before handoff to `/plan` or `/coder`
