---
name: diagnose
description: "Disciplined root-cause analysis for bugs and unexpected behavior. Trigger on 'debug', 'fix crash', 'why is this failing', 'unexpected output'. Mandatory 6-phase workflow before any fix."
disable-model-invocation: false
argument-hint: '[symptom description or error trace]'
---

# diagnose

Identify the true root cause through systematic falsification. **DO NOT GUESS.** A hypothesis is a guess until it survives Phase 3.

## Phase 1: Build Feedback Loop

Create a deterministic pass/fail signal.

- **Requirement:** Target < 2s execution.
- **Isolation:** Isolate filesystem, pin seeds/time.
- **Gate:** If you cannot run code, request logs/telemetry. DO NOT proceed without a loop.

## Phase 2: Reproduce

Confirm the bug matches the report. Achievement of >50% reproduction rate is mandatory before hypothesis testing.

## Phase 3: Hypothesize & Falsify (Parallel Split)

- Read `references/phases.md` for guidance on the scientific falsification method before generating hypotheses.

1. **Generate Hypotheses:** 3-5 falsifiable hypotheses using Bayesian priors (Recent Changes > Logic > Env).
2. **Format:** \"If [X] is the cause, then [Y] will change when I do [Z].\"
3. **Dispatch Gate:** If hypotheses are independent (i.e., they test different modules, layers, or subsystems that don't share state), invoke `multi-agent-dispatch` to test in parallel.

## Phase 4: Instrumentation (Targeted Probes)

Instrument code dynamically.

- **Tagging:** Prefix all debug logs with `[DEBUG-XXXX]`.
- **Method:** Use targeted probes (logs/REPL) at decision boundaries. NEVER \"log everything.\"
- **Performance:** Use profilers (`time.perf_counter`), NOT logs.

## Phase 5: Red-Green Fix

1. **Write Regression Test:** Target the failing seam **before** the fix.
2. **Confirm RED:** Confirm the test fails.
3. **Apply Fix:** Implement minimal changes on a working copy.
4. **Confirm GREEN:** Confirm the test passes.

## Phase 6: Finalization

- [ ] **De-instrument:** Remove all `[DEBUG-XXXX]` tags.
- [ ] **Verification:** Verify fix via the Phase 1 loop.
- [ ] **Clean-up:** Delete throwaway scripts or promote to test suite.

## Transition

- **From Verification:** If triggered by a regression in `verification-before-completion`, return to that skill after Phase 6 for re-verification.
- **From Implementation:** If triggered during `test-driven-development` or `multi-agent-development`, return to the current task/phase in the parent skill.

## Required Final Output

```markdown
## Diagnosis Summary

- **Symptom:** [Description]
- **Root Cause:** [Correct Hypothesis]
- **Fix:** [Changes]
- **Feedback Loop:** [Reproduction Script]

## Post-Mortem

- **Prevention:** [Architecture/Test improvement]
- **Next Steps:** [Follow-up tasks]
```

## Critical Rules

- **NEVER** apply multiple changes simultaneously. One hypothesis per run.
- **NEVER** modify the original source directly. Use a working copy.
- **NEVER** accept \"works on my machine\" as a root cause. The environment delta IS the bug.
