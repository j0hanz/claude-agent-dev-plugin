---
description: Generate a Mermaid diagram for a plugin component, flow, or architecture
argument-hint: <component or system to diagram>
---

# Diagrams

Generate a Mermaid diagram for: $ARGUMENTS

Use the diagrams skill to produce visual documentation of agents, hook flows, skill interactions, or plugin architecture. Output is a Mermaid code block ready to paste into README, ADR, or a docs file.

Agents: !`ls agents/`
Skills: !`ls skills/`
Hook handlers: !`ls hooks/handlers/`
Hook config: @hooks/hooks.json

## When to Use

- Documenting how a new agent or skill fits into the existing plugin architecture
- Visualizing hook lifecycle flow for debugging or onboarding
- Creating an ADR or README section that needs a visual component
- Explaining a multi-step process (e.g., PR flow, context loading sequence)
- Before a refactor, to map the current structure and spot dependencies

Prefer prose documentation for simple one-level descriptions. Use diagrams when relationships between components are the point.

## Execution Steps

1. Invoke the diagrams skill: `Skill("diagrams", "$ARGUMENTS")`
2. Verify the diagram is accurate against actual files (agents/, skills/, hooks/)
3. If the diagram represents architecture, offer to write it to docs/ or update AGENTS.md

## Troubleshooting

**Diagram references a component that doesn't exist** — The skill may hallucinate names. Cross-check every node against the loaded file listings before accepting.

**Mermaid syntax errors when rendering** — Common causes: spaces in node IDs, unclosed brackets, or unsupported diagram type. Ask the skill to simplify to a flowchart if another type fails.

**hooks/handlers/ path not found** — Run `ls hooks/` to confirm the handlers directory name and adjust the context load above accordingly.

**Diagram is too large to read** — Scope it: ask the skill to limit the diagram to one layer (e.g., "only the hook lifecycle, not the full agent graph").

## Success Criteria

- Diagram accurately reflects current codebase structure
- Mermaid syntax is valid (no unclosed blocks)
- All referenced components exist in the repo
- Diagram is understandable without additional explanation

A good diagram replaces a paragraph of explanation — if you still need to explain it, simplify it.
