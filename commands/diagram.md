---
description: Generate a Mermaid diagram for a plugin component, flow, or architecture
argument-hint: <component or system to diagram>
---

# Diagrams

Generate a Mermaid diagram for: $ARGUMENTS

Produces a Mermaid code block ready to paste into README, ADR, or docs. Use for agents, hook flows, skill interactions, or plugin architecture.

Agents: !`ls agents/`
Skills: !`ls skills/`
Hook handlers: !`ls hooks/handlers/`
Hook config: @hooks/hooks.json

## Usage

- Documenting how a new agent or skill fits into the plugin architecture
- Visualizing hook lifecycle flow for debugging or onboarding
- Creating an ADR or README section that needs a visual component
- Explaining a multi-step process (PR flow, context loading sequence)
- Before a refactor, to map current structure and spot dependencies

## Execution Steps

1. Invoke the diagrams skill: `Skill("diagrams", "$ARGUMENTS")`
2. Verify the diagram is accurate against actual files (agents/, skills/, hooks/)
3. If the diagram represents architecture, offer to write it to docs/ or update AGENTS.md

## Troubleshooting

**Diagram references a nonexistent component** — Cross-check every node against the loaded file listings before accepting.

**Mermaid syntax errors when rendering** — Common causes: spaces in node IDs, unclosed brackets, unsupported diagram type. Simplify to a flowchart if another type fails.

**hooks/handlers/ path not found** — Run `ls hooks/` to confirm the handlers directory name and adjust accordingly.

**Diagram is too large to read** — Scope it: "only the hook lifecycle, not the full agent graph."

## Success Criteria

- Diagram accurately reflects current codebase structure
- Mermaid syntax is valid (no unclosed blocks)
- All referenced components exist in the repo
- Diagram is understandable without additional explanation
