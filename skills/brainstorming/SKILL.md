---
name: brainstorming
description: "Structured requirements discovery before implementation. Trigger on 'let's build', 'new feature', 'we need a new', 'I want to implement', 'add X to', 'create a Y', ambiguous design, or unclear terminology — even when the user says 'just build it'. Proactively offer before any implementation begins. Prevents rework by catching problems early."
---

# brainstorming

Structured discovery to prevent rework. Always run for new features or ambiguous requirements.

## Phase 1: Discovery

1. **Stakeholder Probe:** Ask who uses the feature (end users, internal, systems?).
2. **Codebase Scan:**
   - Read `references/codebase-scanner-prompt.md` before dispatching.
   - Dispatch `general-purpose` subagent with the prompt.
   - **Integration**: Upon subagent completion, extract the "Contextual Findings," "Potential Blockers," and "Architectural Fit" sections. These MUST be used to ground the Understanding Statement.
3. **Understanding Statement:** Summarize what was found, constraints, and Key Unknowns. Ask for confirmation.
4. **Adaptive Routing:**
   - **Scope S + No Unknowns:** Jump to Phase 4 (Design).
   - **Scope XL:** Offer to split into sub-features.
   - **Ambiguous Terms:** Run Phase 2 (Clarity).

## Phase 2: Domain Clarity (Term Definition)

- **Constraint:** One term at a time. Ask for definition, context, and usage.
- **Goal:** Resolve conflicts between code, docs, and team language.
- **Exit:** Document in `glossary.md` or `CONTEXT.md`.

## Phase 3: Expert Clarification (Techniques)

Select 1-2 techniques (max 4 questions total):

- **Why:** 5-Whys to find hidden motivation.
- **Premortem:** Imagine failure — what went wrong?
- **Success Logic:** Define success behavior without using "functional".
- **Anti-Scope:** Explicitly what we are NOT building.
- **Trust Breach:** How would an attacker abuse this?

## Creative Checkpoint (Before Design)

- Is there a zero-code solution (config, existing extension)?
- Did an analogous feature already solve this?
- What is the 10x simpler version?

## Phase 4: Design Proposal

1. **Dispatch:** Spawn `design-proposer` agent (`references/design-proposer-prompt.md`) with compressed scan report and discovery findings.
2. **Present:** Offer competing approaches with grounded tradeoffs.
3. **Approval Gate:** Wait for explicit commitment to one approach. Do not guess.

## Phase 5: Transition (Design Brief)

Produce mandatory `markdown-kv` brief:

- **Chosen Approach:** [Name + Letter]
- **Why:** [Key Tradeoff]
- **Scope:** [In-scope vs. Out-of-scope]
- **Constraints:** [Stack, Timeline, Compliance]
- **Interface:** [Input/Output surface]
- **Architecture:** [Components + Responsibilities]
- **Risk Register:** [Risk/Likelihood/Mitigation table]
- **First Step:** [Single concrete action]

## Red Flags

- Skipping brainstorming because "it's obvious".
- Assumed terminology (e.g., Account vs. Customer).
- Capturing "HOW" (code) before "WHAT" (domain).
  mization and rigid designs.
- **NEVER** proceed without an explicit Approval Gate: Proceeding on assumptions guarantees misalignment with user intent.
