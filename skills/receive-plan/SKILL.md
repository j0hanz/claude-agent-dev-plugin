---
name: receive-plan
description: "Verifies any plan/specs pair — whether drafted by request-plan or hand-written by a human — using a blind multi-agent critique panel plus a dedicated Traceability Auditor with real grep/file-read access, gated by an independent Arbiter, producing an APPROVED/REVISE verdict and a plan/NAME.review.md audit trail. Trigger on: 'receive-plan', 'check my plan', 'is this plan ready', 'verify this spec', 'review this plan'. Also triggers when a plan/spec pair already exists and needs validation before execution. Always prefer this skill over request-plan when a plan already exists; prefer request-plan instead when no plan exists yet and one must be drafted."
disable-model-invocation: false
user-invocable: true
argument-hint: '[path to plan.md / specs.md, or "the plan I just wrote"]'
---

# receive-plan

Verify a plan/specs pair of ANY origin before it reaches execution skills. Never drafts or edits a plan itself — only verifies, and routes fixes back to whoever owns the content.

## Process Flow

```
Start: Plan/Specs Pair Received -> 1. Identify Origin (request-plan / hand-written)
  -> 2. Critique Panel (blind, parallel) + Traceability Auditor (always runs)
  -> 3. Arbiter Gate
       -- Auditor N_checked < N_total (any category) ----> automatic REVISE, no exceptions
       -- Auditor complete + panel High/Med unresolved ---> REVISE
       -- APPROVED -----------------------------------------> 4. Finalize
  -- REVISE, round-trip < 2 ---> back to 1 (origin fixes, re-submit)
  -- REVISE, round-trip == 2 ---> Escalate to user with unresolved-findings diff
```

## Step 1: Identify Origin

- **`request-plan` (same session)**: REVISE loops back to its Synthesizer automatically.
- **Hand-written / human-authored**: REVISE surfaces itemized fixes to the user, waits for re-submission.
- **No third initial origin**: `architecting` never hands off to this skill directly — it always routes through `request-plan` first (which then hands off here unconditionally). A REVISE on a plan that started from an `architecting` brief still loops back through `request-plan`'s Synthesizer, with the original brief wrapped in `<untrusted_context>` as one additional candidate — but that's a REVISE-time re-routing, not an initial entry path.
- Untrusted Content: wrap any non-session-originated plan content in `<untrusted_context>` tags before giving it to any panel seat.

## Step 2: Critique Panel + Traceability Auditor

Dispatch in ONE message — fan-out per `../multi-agent-dispatch/SKILL.md` — blind to each other, using the named `researcher` agent (`agents/researcher.md`) for all read-only panel seats (or `spec-reviewer` for spec correctness):

- **Spec-Correctness**: is the spec's content complete and internally sensible? (Dispatch `agents/spec-reviewer.md`).
- **Dependency-Correctness**: does the TASK dependency order make sense; any illogical sequencing? (Dispatch `agents/researcher.md`).
- **Scope-Risk**: is any task oversized, underspecified, or carrying unflagged risk? (Dispatch `agents/researcher.md`).
- Skip these 3 seats entirely at `sketch` depth — too small a stake to spend a semantic panel on. Depth is only known when `request-plan` confirmed it this session; if no depth is known (hand-written origin, or no record of Step 0 having run), default to `contract` and never skip the panel.
- **Traceability Auditor** (always runs, every depth): real `grep`/file-read tool access, mechanical-only checklist: (Dispatch `agents/researcher.md`):
  - Every `Satisfies: REQ-xxx` resolves to a REQ actually defined in specs.md.
  - Every `Depends on: TASK-NNN` resolves to a real task; dependency graph is acyclic.
  - Every Task Block has all 7 required fields present (`Depends on`, `Files`, `Symbols`, `Satisfies`, `Action`, `Validate`, `Expected result` — per `request-plan`'s Canonical Task Block Schema).
  - Every cited file/symbol path actually exists on disk (via grep/file read — read-only, never execute `Validate:` commands; see Strict Rules).
  - Required report format: `N_checked / N_total` per check category, plus the raw grep/file-read output as an appended transcript — a human-inspectable audit trail in `plan/NAME.review.md`, not something the Arbiter itself re-parses.

## Step 3: Arbiter Gate

Dispatch one independent Arbiter agent (using the named `researcher` agent `agents/researcher.md`), given the panel's findings plus the Auditor's report.
Mechanical rule (no semantic judgment needed for this part): if any Auditor category shows `N_checked < N_total`, automatic REVISE — incomplete coverage is never silently treated as "clean."
Otherwise: resolve every panel High/Med finding as Accept&Revise or Reject-with-rationale; REJECT requires a named technical reason, never an empty rejection.
Cap: 2 REVISE round-trips total. On the 2nd unresolved REVISE, escalate to the user with the unresolved-findings diff instead of looping again.

## Step 4: Finalize

On APPROVED: flip the plan's header `Status: DRAFT` → `Status: APPROVED`. Write `plan/NAME.review.md` (Arbiter verdict + Auditor checklist + transcript). Hand off the file paths to `multi-agent-development` / `multi-agent-dispatch` / `test-driven-development` — read their own SKILL.md for how each consumes the plan, since none of them formally documents parsing the Canonical Task Block Schema.
Staleness: any manual edit to an `APPROVED` plan after this point invalidates the `Status: APPROVED` marker (documented convention, not enforced in code). A resubmitted stale plan re-enters at Step 1 as if newly received.

## REVISE Output Format (mandatory)

Always itemize every failing check with file:line / REQ-id / TASK-id specificity — never a bare pass/fail summary. Mechanical checks (Traceability Auditor) are naturally itemizable; require the same specificity from the qualitative seats.

## Strict Rules (NEVER)

- **Self-Verify**: NEVER let `request-plan`'s Synthesizer's own advisory cross-check substitute for this skill's gate.
- **Trust Without Counts**: NEVER accept "zero findings" from the Traceability Auditor without `N_checked == N_total` in the same report.
- **Execute Validate**: NEVER run a plan's `Validate:` command during traceability checking — read/grep only.
- **Endless Loops**: NEVER exceed 2 REVISE round-trips without escalating to the user.
- **Edit the Plan**: NEVER draft or rewrite plan content yourself — route fixes back to the origin (Step 1).

## Next Skills

- **multi-agent-development**: Sequential/dependent execution once APPROVED.
- **multi-agent-dispatch**: Independent-task execution once APPROVED.
- **test-driven-development**: Single focused feature once APPROVED.
- **request-plan**: If REVISE traces back to missing content, not just a fixable error.
