# Validation Guide

Run `cli.py validate` after authoring each artifact and after every `cli.py sync` run.

```bash
python <skill-dir>/scripts/cli.py validate <name>                       # spec only (sketch depth)
python <skill-dir>/scripts/cli.py validate <name> --review              # review gate check
python <skill-dir>/scripts/cli.py pipeline --name <name> --depth contract  # spec+plan+cross (contract/blueprint)
```

`<name>` can be a bare stem (`auth-jwt`) or a full path to either artifact.

## What each mode checks

### `validate` (spec)

- All mandatory sections present for the chosen depth (sketch/contract/blueprint)
- Requirements are atomic (no "and" joining two obligations)
- No vague adjectives (fast, robust, lightweight…) without numeric threshold
- REQs have corresponding ACs; ACs have corresponding VALs

### `pipeline` — plan check

- Every task has all six mandatory fields: `Depends on`, `Files`, `Symbols`, `Action`, `Validate`, `Expected result`
- `Files` and `Symbols` are markdown links `[name](path#L42)`, not bare paths
- `Validate` field contains a backtick-wrapped command
- Warning when `Satisfies:` is missing (traceability spine not set)

### `pipeline` — cross check (Traceability Spine)

The `Satisfies:` field is the link between spec requirements and plan tasks. Every plan task has a `Satisfies:` field listing one or more spec IDs:

```markdown
### TASK-003: Implement token signing

Depends on: TASK-002
Files: [src/auth/jwt.ts](src/auth/jwt.ts)
Symbols: [signToken](src/auth/jwt.ts#L24)
Satisfies: REQ-001, SEC-001
Action: Implement JWT signing using the configured secret and RS256 algorithm.
Validate: `npm test -- auth/jwt.test.ts`
Expected result: All 6 tests pass, 0 skipped.
```

`cli.py sync` sets `Satisfies:` automatically when generating stubs — never type it by hand. Never manually edit the `Satisfies:` field of an existing task either; always let `cli.py sync` manage it.

The cross check loads both paired files and checks:

| Check                          | Rule                                                                                                      | Error type                                                               |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **No uncovered requirements**  | Every `REQ/SEC/PERF/COMP` ID from the spec must appear in at least one task's `Satisfies:` field          | `[CROSS] Uncovered requirement: REQ-002`                                 |
| **No orphan tasks**            | Every ID in a `Satisfies:` field must exist in the spec                                                   | `[CROSS] Orphan task: TASK-007 satisfies 'REQ-999' which is not in spec` |
| **AC coverage**                | Every `AC-###` from the spec should map to at least one task (warning if not)                             | Warning: `[CROSS] AC-003 has no corresponding task`                      |
| **No hallucinated skill refs** | Every backtick-quoted skill-name-shaped token must resolve to a real `skills/` directory (warning if not) | Warning: `[CROSS] Backtick token 'xyz' looks like a skill reference...`  |

`CON-###` (constraints) and `VAL-###` (validation commands) are not checked for coverage — they are spec-internal. A requirement is "covered" if any task has that ID in its `Satisfies:` field; one task can satisfy multiple IDs, and one ID can be satisfied by multiple tasks.

Output includes a summary table:

```
Coverage matrix:
  Requirements covered : 5/5
  ACs covered          : 3/3
  Orphan Satisfies IDs : 0
```

**When spec changes after sync:** edit the spec, re-run `python cli.py sync <name>.specs.md` (adds stubs for new IDs only; existing tasks untouched), then re-run `cli.py pipeline --name <name>` to confirm coverage is clean.

The spine turns "the plan should implement the requirements" from prose advice into a machine-checkable contract. A plan that passes the cross check with zero errors provably covers every stated requirement.

## Exit codes

- `0` — all selected checks pass
- `1` — at least one ERROR found (warnings do not affect exit code)

## Fixing common errors

| Error                                                  | Fix                                                                                         |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `Missing mandatory section: Interfaces`                | Add the section; include at least one introductory sentence before sub-headings             |
| `REQ-002 missing fields: Action`                       | Fill the empty field in the task block                                                      |
| `bare path — use markdown links`                       | Replace `src/auth.ts` with `[src/auth.ts](src/auth.ts)`                                     |
| `Uncovered requirement: REQ-003`                       | Re-run `cli.py sync` to add the missing stub, then author it                                |
| `Orphan task satisfies 'REQ-999'`                      | The ID doesn't exist in the spec — fix the typo or remove the Satisfies entry               |
| `Backtick token 'xyz' looks like a skill reference...` | Verify the skill name is real (check `skills/` directory); fix typo or remove the reference |

## UNVERIFIED markers

`cli.py sync` emits `[UNVERIFIED](UNVERIFIED)` in task `Files:` fields. Before the plan is ready for execution, replace each `UNVERIFIED` with a real path from Grep/Glob output, or document why the path is not yet resolvable (e.g., "new file created by TASK-001").

## Quality gate checklist

Before marking a plan ready for execution:

- [ ] `cli.py validate <name>` (spec) — 0 errors
- [ ] `cli.py pipeline --name <name>` — 0 errors, 0 bare-path warnings, coverage matrix complete
- [ ] All `UNVERIFIED` markers resolved or documented
- [ ] Reviewer agent returns `ready_for_execution: true`
