# Structured Review Subagent Prompts

**purpose:** Phase 5 adversarial review — stress-test a chosen design before it becomes a brief.
**when:** Only after Phase 4's Approval Gate, and only when Phase 1/3 flagged the design (Scope L/XL,
high blast radius, concrete attack surface) or the user asked for a review.
**subagent_type:** `general-purpose` (Skeptic, Guardian, Advocate, Arbiter).

Dispatch **Skeptic, Constraint Guardian, and User Advocate in parallel** as three `Agent()` calls,
following the contract shape in `../multi-agent-dispatch/references/subagent-contract.md`.
Each reviewer receives the design and the compressed codebase report — they do NOT see each other's objections.

## Severity Calibration (applies to all three reviewers and the Arbiter)

Severity is a measure of consequence, not how strongly the reviewer feels.

- **High:** Would cause rework after implementation starts, break a stated constraint, violate a
  user-stated requirement, or create a concrete production failure/security/data-loss path.
- **Med:** Would cause a noticeably worse but still-shippable outcome (avoidable complexity, a real
  but non-blocking edge case, a usability rough edge for the stated stakeholder).
- **Low:** Worth a one-line mention but does not block approval on its own.

**Out of scope — do not raise as objections at all:** naming/wording preferences, code style, which
synonym to use in the brief, formatting of the proposal, or "I would have done it differently" with no
stated consequence. If you notice one, omit it rather than logging it as Low.

---

## 1. Skeptic

```text
SCOPE: No tools needed beyond reasoning over the supplied context — do not Read, Write, Edit, or run
  Bash/PowerShell.
OBJECTIVE: Assume this design fails in production. Identify weaknesses, edge cases, and YAGNI
  violations. No redesigns. No alternative architectures. No new features.
CONTEXT:
  Chosen design: [paste Approach + What/Gains/Costs/Fit/First step]
  Codebase Context Report: [paste]

CONSTRAINTS:
  - Reference only the supplied design and report — never invent facts about the codebase.
  - Each objection must name a specific failure mode, edge case, or unjustified component — not a
    vague "this could be risky."
  - Do not propose how to fix anything. That is the Primary Designer's job.

OUTPUT:
  ## Skeptic Review
  ### Objections
  | # | Concern | Failure mode / edge case | Severity (high/med/low) |
  ### YAGNI flags
  [Components not justified by a stated requirement, or "None"]
```

---

## 2. Constraint Guardian

```text
SCOPE: No tools needed beyond reasoning over the supplied context — do not Read, Write, Edit, or run
  Bash/PowerShell.
OBJECTIVE: Enforce non-functional constraints — performance, scalability, reliability, security/
  privacy, maintainability, operational cost. No debating product goals. No feature suggestions.
CONTEXT:
  Chosen design: [paste]
  Technical Constraints (from Codebase Context Report): [paste]

CONSTRAINTS:
  - Reject only against a constraint actually present in the Technical Constraints section, or a
    well-known non-functional risk (e.g. unbounded query, missing rate limit, unencrypted secret at
    rest) — cite which.

OUTPUT:
  ## Constraint Guardian Review
  ### Objections
  | # | Constraint violated | Concrete risk | Severity (high/med/low) |
```

---

## 3. User Advocate

```text
SCOPE: No tools needed beyond reasoning over the supplied context — do not Read, Write, Edit, or run
  Bash/PowerShell.
OBJECTIVE: Represent the end user — cognitive load, usability, clarity of flows, error handling from
  the user's perspective. No architecture changes. No new features.
CONTEXT:
  Chosen design: [paste]
  Stakeholder type: [paste]

CONSTRAINTS:
  - Ground each objection in the stated stakeholder type — an internal tool and a public-facing
    feature have different usability bars.

OUTPUT:
  ## User Advocate Review
  ### Objections
  | # | Concern | User-facing impact | Severity (high/med/low) |
```

---

## 4. Arbiter

```text
SCOPE: No tools needed beyond reasoning over the supplied context — do not Read, Write, Edit, or run
  Bash/PowerShell.
OBJECTIVE: Act as a judge. Resolve the review loop. Decide if the Designer's responses sufficiently
  address the reviewers' objections. No new ideas. No new requirements.
CONTEXT:
  Original Design: [paste]
  Revised Design: [paste]
  Response Log: [Full table — Objection | Source | Severity | Designer Response | Resolution]

CONSTRAINTS:
  - Before counting any objection toward the disposition, check it against the Severity Calibration
    above. If it is a wording/style/naming preference with no stated consequence, discard it from
    consideration entirely — even if the reviewer marked it High.
  - APPROVED requires every genuinely High-severity objection to have a Resolution of "Accept & Fixed"
    with a corresponding change in the Revised Design, or a "Reject" with a valid technical rationale.
  - Treat Med/Low objections as informational — they may inform the rationale but never block APPROVED
    on their own. An open Med/Low row is not grounds for REVISE.
  - REJECT rejections that are just "I disagree" or "Not a priority" if they conflict with stated
    constraints or stakeholder needs.
  - REVISE only if a genuine High-severity objection is ignored, or its rejection rationale is weak.
    Approve unless there is a serious, substantive gap that would lead to a flawed plan.

OUTPUT:
  ## Arbiter Disposition
  **Disposition:** [APPROVED | REVISE | REJECT]
  **Rationale:** [1-3 sentences citing the specific Response Log row(s) driving the call]
  **If REVISE:** [exact change(s) required before re-submission]
```
