---
name: detective
description: Spawn the detective agent to investigate bugs, hunt for latent issues, audit suspicious code, or trace hard-to-find failures — reactive and proactive modes
argument-hint: <symptom | file/directory | "recent changes" | area of concern>
---

# Command: detective

Investigate `$ARGUMENTS` using the detective subagent.

The detective agent is a code-reading specialist. It traces failures, hunts latent bugs, audits suspicious areas, and follows call chains to their root — without cluttering the main context. **It works in two modes based on what you give it:**

- **Reactive** — you have a known symptom or error: `"TypeError at auth/session.ts:142"`
- **Proactive** — you want it to hunt: `"src/payments/"` or `"recent changes"` or `"anything suspicious in the cache layer"`

- Project state: !`git status --short`
- Recent changes: !`git log --oneline -10`
- Open diff: !`git diff --stat HEAD`

Use the Agent tool with subagent_type "detective" and this exact prompt (substituting `$ARGUMENTS`):

---

Investigation target: $ARGUMENTS

## Step 1 — Determine mode

Read the target and pick the right approach:

- If the target is a **known error or symptom** → use reactive diagnosis (phases below)
- If the target is a **file, directory, or vague area** → use proactive bug hunting (scan for latent issues)
- If the target is **"recent changes"** → diff the last 10 commits and hunt for introduced bugs

## Step 2 — Scope

Use Glob and Grep to map the relevant files and call chains. Read every file you'll make a claim about — do not infer from filenames alone.

## Step 3 — Investigate

For **reactive** targets, apply the `/diagnose` skill in strict phase order:

1. Triage: classify (runtime failure / logic bug / quality issue / performance regression)
2. Reproduce: trace the code path from symptom back to root site, citing file:line
3. Hypothesize: 3–5 falsifiable hypotheses ranked by prior (recent changes > logic > config > deps)
4. Confirm: identify the exact decision boundary where the invariant breaks
5. Propose: output a diff or replacement block — do NOT apply it

For **proactive** targets, apply a structured hunt:

1. Map: identify the highest-risk seams (data boundaries, error paths, concurrency, untested branches)
2. Audit: read each seam for: missing guards, off-by-one errors, incorrect assumptions, race conditions, silent failures, unhandled edge cases
3. Rank findings: severity (Critical / High / Medium / Low) + confidence (High / Medium / Speculative)
4. Propose: for each confirmed finding, output a diff or fix block — do NOT apply

## Step 4 — Report

Always conclude with this exact structure:

## Investigation Summary

**Mode:** Reactive | Proactive
**Target:** [what was investigated]

### Findings

| #   | Location    | Issue       | Severity                 | Confidence              |
| --- | ----------- | ----------- | ------------------------ | ----------------------- |
| 1   | `file:line` | description | Critical/High/Medium/Low | High/Medium/Speculative |

### Fix Proposals

For each finding, a diff or replacement block.

### Regression Tests

For each fix, a test that goes RED before the fix and GREEN after.

## Post-Mortem

- **Root pattern:** [what class of bug this is]
- **Prevention:** [what would have caught this earlier]
- **Next Steps:** [follow-up actions or "None"]

---

After the detective agent reports back, present the Investigation Summary and proposed diffs. Ask for approval before applying any changes.

- All findings include exact file path and line number
- Severity and confidence rated for every finding
- Fixes proposed as diffs only — never applied without user approval
- Regression tests included for every proposed fix
- Both reactive (known symptom) and proactive (hunt) modes covered
