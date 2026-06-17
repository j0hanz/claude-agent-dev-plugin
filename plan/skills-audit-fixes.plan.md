# skills-audit-fixes

Spec: [skills-audit-fixes.specs.md](skills-audit-fixes.specs.md)

## Goal

Fix the 9 consolidated findings from the skills audit so every skill in `skills/` is free of text corruption, internal contradictions, and undeclared failure-routing gaps.

## PHASE-001: Implementation

All 9 tasks touch disjoint files and carry no technical dependency on each other — they may be executed in any order or in parallel.

### TASK-001: Remove corrupted duplicate fragment in brainstorming

Depends on: none
Files: [skills/brainstorming/SKILL.md](skills/brainstorming/SKILL.md)
Symbols: none
Satisfies: REQ-001
Action: Delete the truncated duplicate sentence fragment trailing the real sentence at the end of the Troubleshooting section (around lines 282-283), leaving the section ending cleanly on the original sentence.
Validate: `grep -n "daries clear" skills/brainstorming/SKILL.md`
Expected result: No match (empty output, exit code 1).

### TASK-002: Remove duplicated Reference Map entries in skill-builder

Depends on: none
Files: [skills/skill-builder/SKILL.md](skills/skill-builder/SKILL.md)
Symbols: none
Satisfies: REQ-002
Action: Delete the duplicated Reference Map entries (around lines 274-276) that repeat `agents/analyzer.md`, `references/schemas.md`, `references/cowork.md` a second time, including the corrupted line missing its leading backtick. Leave each entry listed exactly once.
Validate: `grep -c "agents/analyzer.md" skills/skill-builder/SKILL.md`
Expected result: Output is `1`.

### TASK-003: Fix github-automation invocation contradiction in multi-agent-development

Depends on: none
Files: [skills/multi-agent-development/SKILL.md](skills/multi-agent-development/SKILL.md)
Symbols: none
Satisfies: REQ-003
Action: At lines 199 and 215, replace the instruction to directly "invoke github-automation to open PR" with an instruction to prompt the user to run `/github-automation` manually, matching the wording pattern already used in `skills/code-review/SKILL.md:228` and `skills/verification-before-completion/SKILL.md:60`.
Validate: `grep -n "invoke github-automation" skills/multi-agent-development/SKILL.md`
Expected result: No match (empty output, exit code 1).

### TASK-004: Relocate multi-agent-development eval fixture

Depends on: none
Files: [skills/multi-agent-development/evals.json](skills/multi-agent-development/evals.json)
Symbols: none
Satisfies: REQ-004
Action: First grep the repo for any reference to the literal path `multi-agent-development/evals.json` (outside the file itself) to check for external tooling dependencies. If none found, create `skills/multi-agent-development/evals/` and move `evals.json` into it, matching the convention used by the other 15 skills.
Validate: `test -f skills/multi-agent-development/evals/evals.json && test ! -f skills/multi-agent-development/evals.json && echo OK`
Expected result: Output is `OK`.

### TASK-005: Add named diagnose transition to verification-before-completion

Depends on: none
Files: [skills/verification-before-completion/SKILL.md](skills/verification-before-completion/SKILL.md)
Symbols: none
Satisfies: REQ-005
Action: In the "If verification cannot complete" / failure-handling section, add an explicit instruction: if a regression or failing test is found during verification, invoke `diagnose` before re-attempting completion (rather than only marking INCOMPLETE and surfacing to the user with no named next skill).
Validate: `grep -n "diagnose" skills/verification-before-completion/SKILL.md`
Expected result: At least one match.

### TASK-006: Name concrete FAIL targets in code-review

Depends on: none
Files: [skills/code-review/SKILL.md](skills/code-review/SKILL.md)
Symbols: none
Satisfies: REQ-006
Action: Replace the unnamed "FAIL → route back to implementation" instruction (line 229) with a tiered routing rule: correctness/security blocking issues → invoke `diagnose`; structural blocking issues → invoke `refactor`; otherwise → return to the originating implementation skill.
Validate: `grep -niA2 "FAIL" skills/code-review/SKILL.md | grep -i "diagnose\|refactor"`
Expected result: At least one match.

### TASK-007: Add attempt cap to diagnose re-diagnose loop

Depends on: none
Files: [skills/diagnose/SKILL.md](skills/diagnose/SKILL.md)
Symbols: none
Satisfies: REQ-007
Action: In the Troubleshooting section's "Fix applied but tests still fail" / "New failures appear after fix" guidance (around lines 148-152), add a numeric attempt cap mirroring multi-agent-development's pattern: after 2 re-diagnose attempts, stop and surface to the user as BLOCKED instead of re-diagnosing indefinitely.
Validate: `grep -nE "[0-9]+ (attempt|fix attempt)" skills/diagnose/SKILL.md`
Expected result: At least one match.

### TASK-008: Resolve orphaned estimate_risk.py in architecture

Depends on: none
Files: [skills/architecture/scripts/estimate_risk.py](skills/architecture/scripts/estimate_risk.py), [skills/architecture/SKILL.md](skills/architecture/SKILL.md)
Symbols: none
Satisfies: REQ-008
Action: First grep the whole repo for `estimate_risk.py` to confirm no external tooling references it. Per CON-003, default to **delete** the script (recoverable from git history) since no reference was found in `SKILL.md`'s Phase 1 or Step 4. If a human reviewer instead chooses to wire it in, add a reference to it in `skills/architecture/SKILL.md` Phase 1 or Step 4 instead of deleting.
Validate: `grep -q "estimate_risk.py" skills/architecture/SKILL.md && test -f skills/architecture/scripts/estimate_risk.py && echo WIRED || test ! -f skills/architecture/scripts/estimate_risk.py && echo DELETED`
Expected result: Output is exactly one of `WIRED` or `DELETED`.

### TASK-009: Align parallel-vs-sequential threshold between diagnose and multi-agent-dispatch

Depends on: none
Files: [skills/diagnose/SKILL.md](skills/diagnose/SKILL.md), [skills/multi-agent-dispatch/SKILL.md](skills/multi-agent-dispatch/SKILL.md)
Symbols: none
Satisfies: REQ-009
Action: In diagnose's Phase 3 mandatory-dispatch language, add the carve-out already present in multi-agent-dispatch's dispatch gate: a single domain/hypothesis you already fully understand should be tested sequentially, not via dispatch. Reference multi-agent-dispatch's existing wording rather than inventing new phrasing.
Validate: manual diff review — confirm both files now state the same threshold in equivalent terms.
Expected result: No contradiction remains between the two files' stated thresholds.

## PHASE-END: Acceptance

### TASK-010: Final acceptance verification

Depends on: TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009
Files: none
Symbols: none
Satisfies: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009
Action: Run every VAL command from the spec in sequence and confirm each Expected result. Manually re-read each edited file in full to confirm CON-001 and CON-002 were respected (no incidental rewording, no files touched outside the 9 findings).
Validate: `grep -n "daries clear" skills/brainstorming/SKILL.md; grep -c "agents/analyzer.md" skills/skill-builder/SKILL.md; grep -n "invoke github-automation" skills/multi-agent-development/SKILL.md; test -f skills/multi-agent-development/evals/evals.json && test ! -f skills/multi-agent-development/evals.json; grep -n "diagnose" skills/verification-before-completion/SKILL.md; grep -niA2 "FAIL" skills/code-review/SKILL.md | grep -i "diagnose\|refactor"; grep -nE "[0-9]+ (attempt|fix attempt)" skills/diagnose/SKILL.md`
Expected result: All 9 AC items confirmed observable; no unrelated diffs found in manual review.
