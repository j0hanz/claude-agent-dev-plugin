---
name: brainstorming
description: >
  Structured requirements-discovery workflow to prevent rework on new features.
  Use when: a user asks to build, add, or implement anything non-trivial; requirements
  are ambiguous or terminology is unclear; or a stakeholder probe / glossary definition
  is needed. Do NOT use for bug fixes, typos, or config tweaks with no design space.
  Trigger keywords: 'new feature', 'let\'s build a feature', 'I want to implement',
  'add X to', 'ambiguous design', 'unclear terminology', 'requirements discovery',
  'brainstorming', 'stakeholder probe', 'glossary definition'.
---

# brainstorming

Structured discovery to prevent rework. Always run for new features or ambiguous requirements.

<HARD-GATE>
Do not propose code, file changes, or a concrete implementation plan for a new feature or ambiguous
request until Phase 6 produces an approved Design Brief. Sketching the approach in a doc is still
Phase 4 — it still needs Phase 1 Discovery first. Does not apply to bug fixes, typos, or one-line
config changes with no design space.
</HARD-GATE>

**"This is trivial to need discovery"** is the rationalization that defeats this skill most often:
a request that looks trivial can still hide unstated stakeholders, terminology conflicts, or existing
analogous code that Phase 1 would have surfaced. If a request truly has zero ambiguity and one obvious
implementation, say so explicitly and name which step (Stakeholder Probe, Codebase Scan, Understanding
Statement) is skipped and why — never skip silently.

Default subagent type for every dispatch below: `general-purpose`. Type is only called out where it differs.

## Process Flow

```
0. Resume Check
  -- no match -------> 1. Discovery
  -- resume at 2 -----> 2. Domain Clarity
  -- resume at 3 -----> 3. Expert Clarification
  -- resume at 4 -----> 4. Design Proposal
  -- resume at 5 -----> 5. Structured Review

1. Discovery
  -- ambiguous terms -------> 2. Domain Clarity
  -- needs clarification ---> 3. Expert Clarification
  -- scope S, no unknowns ---> 4. Design Proposal

2. Domain Clarity -> 3. Expert Clarification -> 4. Design Proposal

4. Design Proposal
  -- flagged: scope L/XL, high risk, or attack surface --> 5. Structured Review
  -- not flagged -----------------------------------------> 6. Design Brief

5. Structured Review
  -- approved -----> 6. Design Brief
  -- rejected -----> back to 4. Design Proposal
  -- revise (loop) -> back to 5. Structured Review
```

## Phase 0: Resume Check

Before Discovery, check for an in-progress session on this topic.

1. **Check:** Glob `.brainstorm/*.memlog.md`; match by the `topic:` frontmatter field against the current request. No match → proceed to Phase 1; no file is created yet.
2. **Match found:** Read it in full, once. Reconstruct: last completed phase, Understanding Statement, glossary entries, Phase 5 flag + reason, chosen approach, open Response Log rows, pending reviewer dispatches.
3. **Confirm with the user:** "Resuming '[topic]'. We left off at [phase], with [flag/approach state]." Ask to continue, restart, or abandon.
   - **Continue:** Resume at the first incomplete phase. Re-dispatch only reviewers marked pending in Phase 5 — never re-dispatch one whose objections are already logged.
   - **Restart:** Rename the old log with a `.bak-<timestamp>` suffix, proceed to Phase 1 fresh.
   - **Abandon:** Set `status: abandoned` in the frontmatter, stop.
4. **Log discipline (applies to every phase below):** Create `.brainstorm/<topic-slug>.memlog.md` at the end of Phase 1 (not before — short, never-interrupted sessions don't need one). After every phase completes or a gate resolves, append an entry and update the `phase`/`status`/`updated` frontmatter fields. Phase 5 reviewer returns are logged individually as each one returns, not batched — this is what makes mid-dispatch resume possible. Set `status: done` at the end of Phase 6.

## Phase 1: Discovery

**action: Stakeholder Probe**
Identify the primary users and confirm via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually.

> **Tool check:** If `AskUserQuestion` is unavailable, present the options as a numbered markdown list and ask the user to reply with their choice number.

1. ✅ **Recommended** — [Audience] based on [feature context].
2. **Alternative** — [Secondary Audience] + reason for inclusion.

Skip this question entirely if the request already names a single unambiguous audience (e.g. "add an admin-only export button") — confirming the obvious wastes a turn.

4. **Codebase Scan:**

   > **MANDATORY — READ FIRST**: Read
   > [`references/codebase-scanner-prompt.md`](references/codebase-scanner-prompt.md)
   > in full before dispatching the scan subagent.
   > **Do NOT load** `design-proposer-prompt.md` or `structured-review-prompt.md` at this step.
   - Dispatch the subagent with the prompt (which runs the scan script `scripts/scan_context.py` and pipes it through `scripts/compress_report.py`).
   - **Compress:** Pipe the subagent's raw JSON through `python '<skill-dir>/scripts/compress_report.py'` — this becomes "the compressed scan report" used in Phase 4.
   - **Integration:** Extract "Interface Shapes," "Technical Constraints," "Analogous Features," and "Key Unknowns" from the result. Ground the Understanding Statement in these.
   - **Zero-Code Exit:** If the scan finds an existing feature or config that satisfies the request, present it and offer to exit.

5. **Understanding Statement:** Summarize findings, constraints, and Key Unknowns. Get user confirmation.
6. **Adaptive Routing:**
   - **Scope S + No Unknowns:** Skip to Phase 4.
   - **Scope XL:** Offer to split into sub-features. For a greenfield feature, the scanner's file-count signal will read low even when the request itself names several independent subsystems — weigh the feature description's own breadth, not just the scanner's S/M/L/XL estimate.
   - **Ambiguous Terms:** Run Phase 2.
   - **Scope L/XL or High Blast Radius** (auth, payments, data deletion, external-facing API, or sensitive data flow): Set the Phase 5 flag — this is the canonical trigger condition; Phase 3 and Phase 5 reference it rather than restate it. Confirm it with the user before Phase 4.
   - **Log:** Create `.brainstorm/<topic-slug>.memlog.md` (see Phase 0) with the scope estimate, stakeholder choice, Understanding Statement, and Phase 5 flag state + reason.

## Phase 2: Domain Clarity (Term Definition)

**action: Define Term**
For each ambiguous term, propose a definition via `AskUserQuestion` — the tool supplies a free-text "Other" automatically, so don't add one manually. Batch all ambiguous terms from this request into one `AskUserQuestion` call (one question per term, up to 4) instead of one round-trip per term.

> **Tool check:** If `AskUserQuestion` is unavailable, list each term with its proposed definitions as a numbered markdown list and ask the user to reply with their choice per term.

1. ✅ **Recommended** — [Term]: [Definition] based on [codebase usage/patterns].
2. **Alternative** — [Term]: [Alternative Definition] found in conflicting code/docs usage, if one exists.

- **Goal:** Resolve conflicts between code, docs, and team language.
- **Exit:** If Phase 1's scan found an existing `glossary.md` or `CONTEXT.md`, append the term there. If neither exists, create `glossary.md` at the project root — it is the canonical file for term definitions; `CONTEXT.md` is for architectural/contextual notes, not glossaries.
- **Log:** Append the resolved term and definition to the session log.

## Phase 3: Expert Clarification (Techniques)

Select 1-2 techniques (max 4 questions total):

- **Why:** 5-Whys to find hidden motivation.
- **Premortem:** Imagine failure — what went wrong?
- **Success Logic:** Define success behavior without using "functional".
- **Anti-Scope:** Explicitly what we are NOT building.
- **Trust Breach:** How would an attacker abuse this? A concrete attack surface found here also sets the Phase 5 flag (see Phase 1's Adaptive Routing — the canonical condition).

**Log:** Append the techniques used and key answers to the session log.

## Creative Checkpoint (Before Design)

- Is there a zero-code solution (config, existing extension)?
- Did an analogous feature already solve this?
- What is the 10x less complex version?
- **Proactive Filter:** A zero-code or analogous solution found here becomes "Approach A" in Phase 4 — present it, do not silently drop it.
- **Log:** Append the finding (or "none") to the session log.

## Phase 4: Design Proposal

1. **Dispatch:**

   > **MANDATORY — READ FIRST**: Read
   > [`references/design-proposer-prompt.md`](references/design-proposer-prompt.md)
   > in full before spawning the subagent.
   > **Do NOT load** `codebase-scanner-prompt.md` or `structured-review-prompt.md` at this step.

   Spawn the subagent with the compressed scan report and discovery findings.

2. **Present:** Offer 2-3 competing approaches with grounded tradeoffs.
3. **Approval Gate:** Wait for explicit commitment to one approach. Do not guess.
4. **Review Check:** Phase 5 flag set → run Phase 5 before the brief. Not set → skip to Phase 6.
5. **Log:** Append the approaches presented and the chosen one to the session log.

## Phase 5: Structured Review (Conditional)

Runs only if the Phase 5 flag is set (canonical condition: Phase 1's Adaptive Routing), or the user explicitly asks to "stress test" or "review" the design.

**Parallel Adversarial Loop:** Reviewers run concurrently for objectivity and lower latency.

1. **Dispatch Parallel Stress-Test:**

   > **MANDATORY — READ FIRST**: Read
   > [`references/structured-review-prompt.md`](references/structured-review-prompt.md)
   > in full before dispatching any reviewer subagent.
   > **Do NOT load** `codebase-scanner-prompt.md` or `design-proposer-prompt.md` at this step.

   Spawn the Skeptic, Constraint Guardian, and User Advocate templates from that file as three parallel `Agent()` calls (contract shape: `../multi-agent-development/references/subagent-contract.md`). Each sees only the design and context packet — none sees the others' objections or the designer's internal reasoning.
   - **Log:** Append each reviewer's objections to the session log as it returns, not batched after all three finish — this is what lets an interrupted dispatch resume without re-running reviewers that already answered.

2. **Consolidate & Respond:**
   - Log every objection in a **Response Log** (Objection | Source | Severity | Designer Response | Resolution). Apply the Severity Calibration in `references/structured-review-prompt.md` — discard wording/style objections rather than logging them.
   - Resolve each row: **Accept & Revise** (update the design) or **Reject** (give a technical rationale). No row may stay open.
   - **Log:** Append each resolved row to the session log.
3. **Arbiter Gate:**
   - Dispatch the **Arbiter** (template in `references/structured-review-prompt.md`) with the original design, the revised design, and the full Response Log.
   - It judges whether rejections are valid and revisions actually mitigate the concerns.
   - Returns `APPROVED`, `REVISE` (back to step 2), or `REJECT` (back to Phase 4).
   - **Log:** Append the disposition and rationale.
4. **Exit Gate:** All reviewers invoked, Response Log complete, Arbiter disposition `APPROVED`.

## Phase 6: Transition (Design Brief)

Produce mandatory `markdown-kv` brief and persist it:

- **Chosen Approach:** [Name + Letter]
- **Why:** [Key Tradeoff]
- **Scope:** [In-scope vs. Out-of-scope]
- **Success Criteria:** [Measurable outcomes / Acceptance Criteria]
- **Constraints:** [Stack, Timeline, Compliance, Technical Constraints]
- **Interface:** [Input/Output surface]
- **Architecture:** [Components + Responsibilities]
- **Risk Register:** [Risk/Likelihood/Mitigation table — pull rows from the Response Log if Phase 5 ran]
- **Review Disposition:** [Arbiter's APPROVED + date, or "Phase 5 not triggered"]
- **First Step:** [Single concrete action]

**Persist:** Write the brief to `docs/design/YYYY-MM-DD-<topic>-design.md` in the target codebase (today's date, kebab-case topic slug). Present it in chat first — the file is a durable record for the `planning` handoff, not a substitute for the conversational approval.

**Commit (ask first):** Ask whether to commit the file. Default to **not** committing — this skill runs against arbitrary user codebases, and an uninvited commit is a bigger surprise than a leftover untracked file. Skip the question if the directory isn't a git repo.

**Log:** Append the final brief and set `status: done` in the session log's frontmatter.

**next skills:**

- `planning`: To transform the design brief into a concrete implementation spec and task list.
- `architecting`: To refine boundaries or choose patterns if the design reveals structural complexity.

## NEVER Do

- **NEVER** skip Phase 1 for requests containing the words "simple" or "just" — these words historically correlate with the most expensive rework events because they invite assumed terminology and unstated stakeholders.
- **NEVER** assume shared terminology without Phase 2 — "Account" vs. "Customer", "User" vs. "Member" have derailed entire implementations when resolved only at code-review time.
- **NEVER** capture HOW (architecture, code) before WHAT (domain) — a design that skips Discovery produces the right answer to the wrong question.
- **NEVER** approve a Phase 5-flagged design without a separate Arbiter dispatch — the designer agent cannot serve as its own Arbiter; context contamination from Phase 4's internal reasoning invalidates the judgment.
- **NEVER** let the Arbiter approve with unresolved High-severity objections or rejections marked without rationale — an empty "Rejected" row in the Response Log is indistinguishable from a forgotten row.
- **NEVER** let Phase 4 propose an architecture without explicitly citing which Phase 1 constraints it satisfies — a design that doesn't reference constraints has silently ignored them, not consciously addressed them.
- **NEVER** allow a Phase 5 reviewer to propose a redesign — reviewers identify flaws; redesign is Phase 4's job. A reviewer that rewrites the solution has broken the adversarial objectivity the parallel dispatch is designed to preserve.
- **NEVER** re-dispatch a Phase 5 reviewer whose objections are already logged in the session log — re-dispatching resets their context and produces a new, potentially contradictory objection set, corrupting the Response Log.
