---
name: brainstorming
description: "Conducts collaborative discovery, requirements analysis, and system brainstorming before initiating creative implementation or feature building, producing a markdown-kv Design Brief in docs/design/ and session logs in .brainstorm/. Trigger on: 'design a feature', 'add a feature', 'brainstorm a solution', 'write a design doc', 'conduct discovery', 'build a new feature', 'requirements discovery'. Also triggers when request details are ambiguous, require terminology clarity in a glossary, or have unstated stakeholders. Always prefer brainstorming over planning or architecting when requirements are still vague, unproven, or not yet codified into a clear technical specification."
---

# brainstorming

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

- **Pre-Check:** Glob `.brainstorm/*.memlog.md` matching `topic:`. No match → Phase 1.
- **Match Found:** Read file. Reconstruct phase, Understanding Statement, glossary, Phase 5 flag/reason, approach, pending log rows, and pending reviewers.
- **User Prompt:** "Resuming '[topic]'. Left off at [phase], with [state]." Options: Continue, Restart, Abandon.
- **Action Continue:** Resume at first incomplete phase. Re-dispatch ONLY pending reviewers.
- **Action Restart:** Rename old log to `.bak-<timestamp>`. Start Phase 1.
- **Action Abandon:** Update frontmatter `status: abandoned`. Stop.
- **Log Discipline:** Create `.brainstorm/<topic-slug>.memlog.md` post-Phase 1. Append entries and update `phase`/`status`/`updated` frontmatter upon phase completion. Log Phase 5 reviewers individually upon return. Set `status: done` post-Phase 6.

---

## Phase 1: Discovery

- **Stakeholder Probe:** Identify users. Trigger `AskUserQuestion` (1. Recommended, 2. Alternative). Skip if unambiguous.
- **Scanner Subagent:** Dispatch one read-only `general-purpose` agent (Glob/Grep/Read/Bash only — no Write/Edit). Give it the feature description verbatim and the project root, and have it run `python scripts/scan_context.py -- '<sanitized_noun1>' ['<sanitized_noun2>' ...] --cwd '<project_root>' | python scripts/compress_report.py` (extract 2-3 domain nouns/verbs from the feature description, strip shell metacharacters, alphanumeric+hyphen only), falling back to manual Glob/Grep exploration only if the script fails. Ask for a Codebase Context Report: Related Files, Recent Changes, Terminology Found, Interface Shapes, Design Docs, Technical Constraints, Analogous Features, Test Coverage, Scope Signal (S/M/L/XL with reasoning — S=1-2 files, M=3-5, L=5-10 or module boundary, XL=10+ or architectural), Key Unknowns. If the agent times out or the repo is too large, fall back to shallow regex/Grep in the parent context rather than failing the workflow.
- **Extraction:** Interface Shapes, Technical Constraints, Analogous Features, Key Unknowns.
- **Zero-Code Exit:** Offer exit if scan finds existing satisfying feature/config.
- **Understanding Statement:** Summarize extraction. Require user confirmation.
- **Adaptive Routing:**
- Scope S + No Unknowns → Phase 4
- Scope XL → Offer sub-feature split
- Ambiguous Terms → Phase 2
- Scope L/XL or High Blast Radius → Set Phase 5 flag. Confirm with user.

- **Log Entry:** Append scope, stakeholder, statement, and Phase 5 flag.

---

## Phase 2: Domain Clarity

- **Action Define Term:** Batch max 4 ambiguous terms via `AskUserQuestion`. Supply Recommended vs Alternative definitions.
- **Persistence:** Append to `glossary.md` at root (create if missing). Do not use `CONTEXT.md` for terms.
- **Log Entry:** Append resolved terms and definitions.

---

## Phase 3: Expert Clarification

- **Action Techniques:** Select 1-2 techniques (max 4 questions): 5-Whys, Premortem, Success Logic, Anti-Scope, Trust Breach.
- **Trust Breach Result:** Finding concrete attack surface → Set Phase 5 flag.
- **Log Entry:** Append techniques and key answers.

---

## Creative Checkpoint (Pre-Design)

- **Evaluation:** Check for zero-code, analogous features, or a 10x simpler solution.
- **Proactive Filter:** Present zero-code/analogous solutions as "Approach A" in Phase 4.
- **Log Entry:** Append finding (or "none").

---

## Phase 4: Design Proposal

- **Designer Subagent:** Dispatch one reasoning-only `general-purpose` agent (no tools — Read/Write/Edit/Bash all out of scope). Give it the full context packet: feature description, stakeholder type, compressed Codebase Context Report (Analogous Features, Test Coverage, Interface Shapes especially), domain terms, risks/success criteria, Creative Checkpoint finding. Ask for 2-3 approaches that differ on real axes (build vs extend, sync vs async, simple+fast vs robust+complex, conventional vs unconventional) — never naming/minor-detail variants. At least one must be non-obvious/unconventional; the Creative Checkpoint candidate (if any) must be "Approach A". Each approach: What/Gains/Costs/Fit/First step. Recommendation must cite a specific constraint from the report and the success criterion it satisfies — never generic best practice. Unjustified components go in a "Deferred (YAGNI)" list, not silently dropped.
- **Presentation:** 2-3 approaches with grounded tradeoffs.
- **Approval Gate:** Await explicit user commitment to one approach. Do not guess.
- **Review Check:** Phase 5 flag set → Phase 5. Not set → Phase 6.
- **Log Entry:** Append approaches and user choice.

---

## Phase 5: Structured Review

- **Trigger:** Phase 5 flag set OR explicit user request to stress test.
- **Parallel Dispatch:** Run `multi-agent-dispatch` with this Lane Matrix — three read-only, reasoning-only lanes, no files touched, no dependencies between them. Each reviewer sees the chosen design + Codebase Context Report but never another reviewer's objections.

  | Lane | Role                | Objective                                                                                                                                                                                                                            | Output                                                                          |
  | :--- | :------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
  | 1    | Skeptic             | Assume the design fails in production. Find weaknesses, edge cases, YAGNI violations. No redesigns, no alternative architectures, no new features — that's the Designer's job.                                                       | Objections table (Concern / Failure mode or edge case / Severity) + YAGNI flags |
  | 2    | Constraint Guardian | Enforce non-functional constraints — perf, scale, reliability, security/privacy, maintainability, operational cost — against the report's Technical Constraints section or a well-known non-functional risk. No product-goal debate. | Objections table (Constraint violated / Concrete risk / Severity)               |
  | 3    | User Advocate       | Represent the end user — cognitive load, usability, error handling — grounded in the stated stakeholder type. No architecture changes, no new features.                                                                              | Objections table (Concern / User-facing impact / Severity)                      |

  **Severity Calibration** (all three + Arbiter): **High** = causes rework after implementation starts, breaks a stated constraint/requirement, or a concrete production/security/data-loss path. **Med** = shippable but a noticeably worse outcome. **Low** = worth a one-line mention, never blocks alone. Out of scope entirely: naming/wording/style preferences — omit, don't log even as Low.

- **Consolidation:** Create Response Log (Objection | Source | Severity | Designer Response | Resolution). Discard style/wording objections.
- **Resolution:** Accept & Revise (update design) OR Reject (provide technical rationale). No open rows allowed.
- **Arbiter Gate:** One follow-up reasoning-only `general-purpose` agent (no tools) — give it the Original Design, Revised Design, and full Response Log. It must discard any objection that's really a style/naming preference even if marked High, require every genuinely High-severity objection to be "Accept & Fixed" with a matching Revised Design change or "Reject" with valid technical rationale, treat Med/Low as informational only (never blocking on their own), and return `APPROVED | REVISE | REJECT` with a 1-3 sentence rationale citing the specific Response Log row(s) — plus the exact required change(s) if `REVISE`.
- **Exit Condition:** All reviewers invoked, Response Log complete, Arbiter `APPROVED`.
- **Log Entry:** Append reviewer objections (upon individual return), resolved rows, Arbiter disposition, and rationale.

---

## Phase 6: Transition

- **Brief Format:** `markdown-kv` containing: Chosen Approach, Why, Scope, Success Criteria, Constraints, Interface, Architecture, Risk Register, Review Disposition, First Step.
- **Persistence:** Write to `docs/design/YYYY-MM-DD-<topic>-design.md`. Present in chat first.
- **Commit Guard:** Ask before git commit. Default to NO. Skip if not a git repository.
- **Next Skills:** `planning`, `architecting`, `context-optimizer` (if context bloats mid-session).
- **Log Entry:** Append final brief. Update frontmatter `status: done`.

---

## NEVER Do

- **Skip Discovery:** Execute Phase 1 regardless of "simple" or "just" descriptors.
- **Assume Terminology:** Always execute Phase 2 for ambiguities.
- **Capture HOW before WHAT:** Never skip Discovery before Design.
- **Self-Arbitrate:** Designer cannot evaluate its own design in Phase 5.
- **Accept Empty Rejections:** Arbiter requires rationale for rejected High-severity objections.
- **Ignore Constraints:** Phase 4 architecture must explicitly cite which Phase 1 constraints it satisfies.
- **Reviewer Redesign:** Phase 5 reviewers only identify flaws; Phase 4 handles redesign.
- **Re-dispatch Reviewers:** Never re-run a Phase 5 reviewer if objections are already logged in the session log.
