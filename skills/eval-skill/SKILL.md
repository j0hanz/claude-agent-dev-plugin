---
name: eval-skill
description: "Behavior-tests an existing skill by measuring whether its description reliably triggers on realistic prompts and whether invoking it produces the correct route and artifacts, driving the existing tests/skill-triggering harness (run-test.sh + grade-transcript.mjs) and per-skill evals.json cases. Use this to test skill behavior; use make-a-skill instead for scaffolding or structural validation of a skill, and test-driven-development for testing application code. Trigger on: 'test if this skill triggers', 'eval this skill', 'does my skill fire', 'skill trigger rate', 'write evals for a skill', 'eval-skill'."
disable-model-invocation: false
---

# eval-skill

Behavior-test an existing skill: does its description trigger on realistic prompts, and does
invoking it produce the right route and artifacts? Pairs with `make-a-skill`, which only
checks structure — this checks behavior. It reuses the harness in `tests/skill-triggering/`
(`run-test.sh` + `grade-transcript.mjs`); it never builds a parallel runner.

## When NOT to use

- Scaffolding, drafting, or structural-lint of a skill → `make-a-skill`.
- Testing application code under a test-first cycle → `test-driven-development`.

## Process Flow

```
1. Pick target skill + find coverage gap
  -> 2. Author evals.json cases (naive prompts + checkable expectations)
  -> 3. Run the harness
  -> 4. Interpret
       -- NOT triggered ----> description problem (fix description field) -> back to 3
       -- graded FAIL ------> body problem (fix SKILL.md procedure) ------> back to 3
       -- all PASS ---------> wire into package.json test:eval
```

## Step 1: Pick target & find the gap

- If the target skill is ambiguous, confirm it via `AskUserQuestion`.
- Coverage check: look for `skills/<name>/evals/evals.json` and
  `tests/skill-triggering/prompts/<name>.txt`. Skills with neither are untested — at time of
  writing that includes `codebase-init`, `context-optimizer`, `make-a-skill`, and
  `receive-code-review`.
- Name the failure mode you're testing: **triggering** (does it fire at all?) vs. **output**
  (does it do the right thing once fired?).

## Step 2: Author eval cases

- Write `skills/<name>/evals/evals.json`: a JSON array of `{ "id", "prompt", "expectations": [] }`.
- `prompt`: a realistic, naive user request that _should_ trigger the skill — no skill name,
  no internal jargon. Match the naive style of the existing `prompts/*.txt` files.
- `expectations`: specific, checkable claims about the response (route taken, artifact written,
  gate enforced). `grade-transcript.mjs` reads these.
- When debugging _over_-triggering, also add a near-miss prompt that should NOT fire it.

## Step 3: Run the harness

- One skill: `bash tests/skill-triggering/run-test.sh <name> tests/skill-triggering/prompts/<name>.txt`
  — if `evals.json` exists, the script runs the evals loop and grader automatically; otherwise
  it falls back to the static prompt file.
- All wired skills: `bash tests/skill-triggering/run-all.sh`.
- Requires the `claude` CLI on `PATH`; each case runs `claude -p --plugin-dir . --max-turns 3`.

## Step 4: Interpret & route the fix

- **NOT triggered** → description problem. Rewrite the `description` field's trigger phrases
  (hand to `make-a-skill` Step 4, which owns descriptions); re-run.
- **Triggered but graded FAIL** → body problem. Fix the `SKILL.md` procedure; re-run.
- **Flaky across runs** → tighten trigger phrases or expectations. Never accept a sub-100%
  trigger rate as passing.
- Once coverage is lasting, add it to `package.json` `test:eval` so `npm test` exercises it.

## NEVER

- **NEVER** build a second eval runner. **WHY:** `run-test.sh` + `grade-transcript.mjs` already
  do it. **FIX:** add `evals.json` cases instead.
- **NEVER** assert a skill "works" from reading it. **WHY:** triggering is probabilistic.
  **FIX:** run the harness and read the transcript.
- **NEVER** put the skill name in an eval prompt. **WHY:** real users don't name skills, so it
  tests nothing. **FIX:** naive prompts only.

**next skills:**

- `make-a-skill`: if the target skill needs structural fixes, a rewritten description, or doesn't exist yet.
- `context-optimizer`: if context bloats mid-skill (long transcript reads, many runs).
