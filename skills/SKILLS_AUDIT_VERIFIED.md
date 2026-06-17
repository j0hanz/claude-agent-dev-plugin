# agent-dev Skills Audit — Verified Findings

Follow-up to [SKILLS_AUDIT.md](SKILLS_AUDIT.md). That first pass was produced by three agents reasoning over the skill set; this pass independently verifies those claims against the actual files and adds a fresh bug-hunt pass.

- **general-purpose agent** — fact-checked the 10 specific claims from the first audit against file contents (line numbers, exact quotes)
- **detective agent** — independent bug-hunt across all 16 skills, no reliance on the prior audit

Date: 2026-06-17

---

## 1. Verification of Original Audit Claims

| #   | Claim                                                                                                       | Verdict                                                                                                                                                                                                                                                                        |
| --- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `skill-builder` has duplicated trailing lines (copy-paste artifact)                                         | **CONFIRMED** — lines 273–276 repeat lines 268–273, including an orphaned fragment missing a leading backtick                                                                                                                                                                  |
| 2   | `agents-maintainer` has `disable-model-invocation: true`                                                    | **CONFIRMED** — line 4                                                                                                                                                                                                                                                         |
| 3   | `github-automation` has `disable-model-invocation: true`                                                    | **CONFIRMED** — line 4                                                                                                                                                                                                                                                         |
| 4   | `test-driven-development` description uses generic phrases + proactive triggering + `user-invocable: false` | **CONFIRMED** — verbatim match                                                                                                                                                                                                                                                 |
| 5   | `using-agent-dev-skills` routing table has no broken skill-name references                                  | **CONFIRMED** — all 16 names cross-checked against real directories, no typos                                                                                                                                                                                                  |
| 6   | `multi-agent-development` has bounded 2-attempt retry before `BLOCKED`                                      | **CONFIRMED** — exact "2 fix attempts" language at two gates                                                                                                                                                                                                                   |
| 7   | `multi-agent-dispatch` mandates "no shared mutable state" + worktree isolation                              | **CONFIRMED** — verbatim                                                                                                                                                                                                                                                       |
| 8   | `verification-before-completion` has no failure edge into `diagnose`                                        | **PARTIALLY TRUE** — failure handling _is_ documented (mark INCOMPLETE, surface to user), but it never names `diagnose` specifically. The original audit's "no failure edge at all" framing overstates the gap; the real issue is narrower: no _named transition to diagnose_. |
| 9   | `code-review` FAIL path doesn't name a target skill                                                         | **CONFIRMED** — line 229: "route back to implementation" with no skill named                                                                                                                                                                                                   |
| 10  | `diagnose`'s re-diagnose loop has no attempt cap                                                            | **CONFIRMED** — no numeric cap anywhere in the file, unlike multi-agent-development                                                                                                                                                                                            |

**9 of 10 claims fully confirmed; 1 needs the more precise framing above.**

---

## 2. New Findings (independent detective pass)

| Severity    | Location                                               | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ----------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🔴 Critical | `brainstorming/SKILL.md:282-283`                       | Literal text-corruption copy-paste artifact at the end of the Troubleshooting section — a truncated duplicate fragment ("daries clear, key design decisions documented...") trailing the real sentence. Ships to every agent that loads this skill.                                                                                                                                                                                                              |
| 🔴 Critical | `skill-builder/SKILL.md:267-277`                       | Confirms claim #1 above with more detail: the Reference Map list duplicates its last 3 entries a second time, with the duplicate's first line missing its leading backtick — renders as broken markdown.                                                                                                                                                                                                                                                         |
| 🟡 Moderate | `multi-agent-development/SKILL.md:199,215`             | Contradicts `github-automation`'s own invocation contract. Tells the agent to "invoke github-automation to open PR" as an unconditional autonomous step, but `github-automation/SKILL.md:4` sets `disable-model-invocation: true` — every other skill that reaches this point (`code-review:228`, `verification-before-completion:60`) correctly says to prompt the user to run `/github-automation` manually instead. This is the one skill that gets it wrong. |
| 🟡 Moderate | `multi-agent-development/evals.json`                   | Stored at the skill root instead of `evals/evals.json` like all 15 other skills. Any tooling that walks `skills/*/evals/evals.json` will silently skip this skill's eval suite.                                                                                                                                                                                                                                                                                  |
| 🟢 Minor    | `architecture/scripts/estimate_risk.py`                | Orphaned script — exists alongside 5 other scripts that are all referenced from `SKILL.md`, but this one is never mentioned and will never run.                                                                                                                                                                                                                                                                                                                  |
| 🟢 Minor    | `diagnose/SKILL.md` vs `multi-agent-dispatch/SKILL.md` | Soft contradiction: diagnose Phase 3 says mandatory parallel-hypothesis dispatch is required and sequential testing is "an anti-pattern," while multi-agent-dispatch's own gate says a single domain you already understand should stay sequential. Not a broken reference, but the two skills disagree on the threshold for when parallelism is warranted in a 1–2 hypothesis diagnose case.                                                                    |

**Detective's overall verdict:** structurally sound (no broken file references, no misspelled cross-skill names, consistent frontmatter), but two skills ship literal text corruption and `multi-agent-development` has both a real invocation contradiction and a non-conforming eval file path.

---

## 3. Consolidated Findings (deduplicated, ranked)

1. **🔴 `brainstorming/SKILL.md:282-283`** — remove the corrupted duplicate sentence fragment.
2. **🔴 `skill-builder/SKILL.md:267-277`** — remove the duplicated Reference Map entries (lines 274-276) and fix the missing backtick.
3. **🟡 `multi-agent-development/SKILL.md:199,215`** — change "invoke github-automation to open PR" to match the pattern used elsewhere: prompt the user to run `/github-automation` manually, since it's `disable-model-invocation: true`.
4. **🟡 `multi-agent-development/evals.json`** — move to `multi-agent-development/evals/evals.json` to match the other 15 skills' convention.
5. **🟡 `verification-before-completion`** — add a named transition: "if a regression/failing test is found during verification, invoke `diagnose` before re-attempting completion" (refines the original audit's gap #8 with the precise fix).
6. **🟡 `code-review` FAIL path** — name a concrete target instead of "route back to implementation" (e.g. tiered: correctness/security → `diagnose`, structural → `refactor`, otherwise the originating implementation skill).
7. **🟡 `diagnose` re-diagnose loop** — add an attempt cap mirroring multi-agent-development's "2 attempts → BLOCKED → surface to user" pattern.
8. **🟢 `architecture/scripts/estimate_risk.py`** — either wire it into `SKILL.md` (Phase 1 or Step 4) or delete it if obsolete.
9. **🟢 `diagnose` vs `multi-agent-dispatch`** — align the stated threshold for "how many hypotheses justify parallel dispatch vs sequential testing" so the two skills don't disagree.

---

## 4. Recommended Next Step

Items 1–2 are one-line text deletions and are safe to fix immediately. Items 3–7 are small, targeted edits to existing sections (no new sections needed). Item 8 needs a decision (wire in or delete) before editing. Item 9 needs a one-line threshold clarification in one of the two files (suggest standardizing on multi-agent-dispatch's "single domain you already understand → stay sequential" language, since diagnose's Phase 3 can reference it directly).
