---
name: architecture
description: "Use when a codebase has system-level structural problems (circular deps, God modules, package/service boundary issues) or when designing new systems. Trigger on 'architecture review', 'where should this code live', 'too coupled', 'God class', 'design this system', 'restructure this'."
disable-model-invocation: false
allowed-tools: Bash(node *), Bash(python *), AskUserQuestion
---

# architecture

System-level structural design focused on Reversibility and Boundary Integrity.

## Decision Protocol (Mandatory for ALL Questions)

Route, interview, and confirm via `AskUserQuestion` (or 3-option markdown block) using this exact template:

1. **✅ Recommended — [Concrete Answer]**: Based on [specific evidence: import count, file size, churn, framework].
2. **Also likely — [Plausible Alternative]**: Condition under which this becomes the right call.
3. **Something else (your call)**: Custom user response.

## Mode Selection

- **Mode A: DIAGNOSE**: Existing codebase. Focus: Circular deps, God modules, bleed detection, git coupling.
- **Mode B: DESIGN**: New feature/module. Focus: Boundary integrity, reversibility, pattern selection.

## MODE A — DIAGNOSE: Procedure

1. **Explore (Phase 1)**:
   - Detect tech stack (`package.json`, etc.).
   - Run `check_locality.py`, `detect_bleed.py`, `git_coupling.py`, and `detect_hotspots.py`.
   - **Fallback**: If scripts fail to run, manually analyze imports for circularities, use `grep` to find "God" modules (>500 lines or 20+ exports), and check file history for coupling.
   - Read `references/dispatch-template.md` before dispatching.
   - Dispatch `general-purpose` agent with the template for structural analysis.
2. **Present (Phase 2)**: List 3-6 deepening opportunities. Format: [Short Name], [Files], [The Bleed], [The Deepening], [Impact], [Risk], [Mermaid Diagram].
3. **Align (Phase 3)**:
   - Read `references/DOMAIN_INTERVIEW.md` and conduct the interview.
   - Propose the Seam (New Interface Shape).
     - **Requirement**: The proposal MUST include a TypeScript/Python interface definition, a description of the data flow, and a "Before vs. After" dependency graph (Mermaid).
   - Write `architecture-brief.json` (approach, scope, constraints, interface, first_step).
   - Handoff to `refactor` or `planning`.

## MODE B — DESIGN: Procedure

1. **Diagnose**: Identify Core Domain vs. Mechanism.
2. **Select Pattern**:
   - Read `references/architecture-patterns.md` before proceeding.
3. **Stress Test**: Apply Swap Test (If we swap [mechanism], what changes?).
4. **Scaffold**: Write `architecture-brief.json` and run `scaffold_boundary.py`.
   - **Fallback**: If `scaffold_boundary.py` fails, manually create the directory structure and interface files based on the brief.

## Core Heuristics

- **Deletion Test**: Would removing this module scatter complexity across callers?
- **Seam Test**: Can business logic be tested without I/O (DB/HTTP)?
- **Locality Test**: Can a maintainer understand the module without reading 5+ dependents?
- **Stability Rule**: Outer layers (UI, DB) depend on Domain (Logic), NEVER the reverse.

## NEVER

- No PubSub for direct coupling (use composition).
- No `utils/`, `common/`, or `shared/` grouping (use domain-based grouping).
- No extract base class if composition is possible.
- No shared DB schemas across bounded contexts.
