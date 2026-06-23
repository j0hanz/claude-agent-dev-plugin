---
name: eval-skill
description: "Runs behavior tests on local skills by executing run-test.sh over prompt txt files and validating outputs using grade-transcript.mjs against assertions in evals.json. Verifies that the LLM routes correctly and produces expected artifact files under the local test suite runner without building parallel runners. Trigger on: 'eval this skill', 'does my skill fire', 'run skill evals', 'eval-skill'."
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

## Step 1: Choose Target & Check Tests

- If the skill's goal is unclear, run `AskUserQuestion`.
- Check for tests: Look for `skills/<name>/evals/evals.json` and `tests/skill-triggering/prompts/<name>.txt`. Missing files mean the skill is untested.
- Pick your test goal: Are you testing if it **starts** (triggering) or if the **result is correct** (output)?

## Step 2: Write Test Cases

- Edit `skills/<name>/evals/evals.json`. Add a JSON list using this format: `{ "id", "prompt", "expectations": [] }`.
- **`prompt`**: Write a normal, everyday user request that should start the skill. Do not use the skill name or tech words.
- **`expectations`**: List exact things that must happen (like writing a specific file).
- **Near-miss**: Add a test that sounds similar but should NOT start the skill.

## Step 3: Run the Tests

- **Test one skill:** Run `bash tests/skill-triggering/run-test.sh <name> tests/skill-triggering/prompts/<name>.txt`.
- **Test all skills:** Run `bash tests/skill-triggering/run-all.sh`.
- _Note:_ You must have the `claude` CLI working.

## Step 4: Fix the Results

- **Did not start?** Fix the `description` trigger words. Run again.
- **Started but failed?** Fix the `SKILL.md` steps. Run again.
- **Unstable (sometimes passes, sometimes fails)?** Make the test rules stricter. It must pass 100% of the time.
- **Complete?** Add the test to `package.json` under `test:eval`.

## NEVER DO THESE

- **NEVER build a new test runner.** Just add test cases to `evals.json`.
- **NEVER guess that a skill works by just reading it.** You must run the test.
- **NEVER use the skill name in a prompt.** Real users do not know the skill names, so it ruins the test.

**next skills:**

- `make-a-skill`: if the target skill needs structural fixes, a rewritten description, or doesn't exist yet.
- `context-optimizer`: if context bloats mid-skill (long transcript reads, many runs).
