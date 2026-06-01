---
name: planning
description: "Full planning pipeline: spec then plan, cross-aligned. Trigger on 'write a spec', 'create a plan', 'what should we build', 'define requirements', 'write specs', 'plan this feature', 'implementation plan', 'spec and plan', 'planning'. Produces two paired artifacts per invocation: <name>.specs.md and <name>.plan.md. Replaces create-specs and create-plan."
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash(python *) Bash(python3 *)
argument-hint: |
  [--depth sketch|contract|blueprint (default: contract)]
  [--spec-only] [--from-spec <file>]
  [--quick] [--assume-paths] [--domain api|cli]
  Examples:
  - /planning "Add JWT authentication"
  - /planning --depth blueprint "High-throughput event pipeline"
  - /planning --spec-only "Define the API contract"
  - /planning --from-spec plan/auth-jwt.specs.md
---

# Planning

Produces two paired, cross-linked artifacts per invocation:

| File                   | What it says                                                     |
| ---------------------- | ---------------------------------------------------------------- |
| `plan/<name>.specs.md` | What must be built, why, interfaces, acceptance criteria         |
| `plan/<name>.plan.md`  | Atomic ordered tasks with verified paths and validation commands |

Every plan task carries a `Satisfies: REQ-001, SEC-002` field that links it back to spec IDs. `validate.py --cross` enforces a coverage matrix: no uncovered requirements, no orphan tasks.

## Depth Dial

| Depth                  | Spec rigor                                        | Plan format       | Use when                   |
| ---------------------- | ------------------------------------------------- | ----------------- | -------------------------- |
| `sketch`               | Goal + top REQs + rough interfaces                | Compact phases    | Early idea, exploratory    |
| `contract` _(default)_ | All 8 sections, interface errors mandatory        | Atomic tasks      | Feature-ready, build-ready |
| `blueprint`            | Contract + rollback, error cases, Mermaid diagram | Narrative runbook | Production-critical        |

## Modifiers

- `--spec-only` — write only `<name>.specs.md`; stop before planning
- `--from-spec <file>` — skip spec authoring, generate plan from an existing spec file
- `--quick` — skip file discovery, assume standard structure
- `--assume-paths` — multi-repo: document path assumptions instead of discovering
- `--domain api|cli` — inject domain-specific requirement + interface snippets

## Pipeline

```
Intake → scaffold.py → Author spec → validate.py --spec
       → sync.py → discover.py → Author plan tasks → validate.py --plan
       → validate.py --cross → reviewer agent → Handoff
```

**Scripts drive the mechanical work; you write prose only.**

| Script | What it does | When to run |
|---|---|---|
| `scaffold.py NAME --depth D` | Emits both paired files with pre-placed IDs | Start of every invocation |
| `sync.py NAME.specs.md` | Reads spec IDs, populates plan task stubs with `Satisfies:` pre-filled (idempotent) | After authoring/editing spec |
| `discover.py --files GLOB --names SYM` | Resolves paths + symbols to verified markdown links | Before filling task Files/Symbols fields |
| `validate.py NAME [--spec --plan --cross]` | Structural + traceability checks; `--cross` = coverage matrix | After authoring each artifact and after sync |

## Step-by-Step Execution

### Step 1 — Intake

Confirm: purpose (what are we adding/fixing?), scope (which component?), constraints (hard limits?).

If vague → ask the 5 Spec Interview questions (see `references/spec-template.md`) before scaffolding.

### Step 2 — Scaffold

```bash
python <skill-dir>/scripts/scaffold.py <name> --depth contract [--domain api|cli] [--goal "..."]
```

Creates `plan/<name>.specs.md` and `plan/<name>.plan.md` with matching ID skeletons.

### Step 3 — Author spec

Fill the scaffolded `<name>.specs.md`. Use `REQ-###`/`SEC-###`/`PERF-###`/`CON-###`/`AC-###`/`VAL-###` labels exactly as placed by scaffold. Never invent IDs by hand.

**GATE:** Run `validate.py --spec` — resolve all ERRORS before continuing.

```bash
python <skill-dir>/scripts/validate.py <name> --spec --level contract
```

Then spawn `agents/reviewer.md` for semantic checks (unmeasured adjectives, compound REQs, interface error gaps).

### Step 4 — Sync plan stubs

```bash
python <skill-dir>/scripts/sync.py plan/<name>.specs.md
```

Populates `<name>.plan.md` with one task stub per requirement, `Satisfies:` pre-filled. Idempotent — safe to re-run after spec edits.

### Step 5 — Discover paths & symbols

For each task that touches real files, run:

```bash
python <skill-dir>/scripts/discover.py --files "src/**/*.ts" --names "functionName"
```

Paste the markdown link output directly into the task `Files:` and `Symbols:` fields.

### Step 6 — Author plan tasks

Fill in each stub's `Action`, `Validate`, and `Expected result`. Rules:

- One task = one observable outcome (no "and" joining two outcomes)
- `Validate:` must be a verbatim shell command in backticks
- `Files:` and `Symbols:` must be markdown links `[name](path#L42)`
- Do NOT edit the `Satisfies:` field — it was set by sync.py

See `references/plan-template.md` for the canonical task block format.

**GATE:** Run `validate.py --plan` — resolve all ERRORS.

```bash
python <skill-dir>/scripts/validate.py <name> --plan
```

### Step 7 — Cross-validate

```bash
python <skill-dir>/scripts/validate.py <name> --cross
```

Checks: every spec requirement covered by ≥1 task; every `Satisfies:` ID exists in spec; every AC mapped. Fix all ERRORS — do not proceed with an uncovered requirement or orphan task.

### Step 8 — Reviewer

Spawn `agents/reviewer.md` with both `spec_path` and `plan_path`. It scores spec quality, plan quality, and traceability together and returns `ready_for_execution`.

### Step 9 — Handoff

Export `plan/<name>.specs.md` + `plan/<name>.plan.md`. The spec says _what_ and _why_; the plan says _how_ and _in what order_. Pass the plan to `test-driven-development` for execution.

## Canonical Task Block

```
### TASK-001: [Action title]

Depends on: [TASK-000](#task-000-title) or none
Files: [path/to/file.ts](path/to/file.ts)
Symbols: [functionName](path/to/file.ts#L42)
Satisfies: REQ-001, SEC-002
Action: Single specific imperative implementation action.
Validate: `npm test -- path/to/file.test.ts`
Expected result: Observable success signal (e.g., "All 8 tests pass").
```

**`Satisfies:` is the spine.** It links this task back to spec IDs. Never remove or edit it after `sync.py` sets it.

## Anti-Patterns

- **Never hand-type a spec ID** — use `scaffold.py` to generate them. Typos create orphans.
- **Never hand-type a file path** — use `discover.py` output. Unverified paths fail at execution.
- **Never edit `Satisfies:` manually** — re-run `sync.py` if requirements change.
- **Never skip `validate.py --cross`** — a plan that passes `--spec` and `--plan` can still have uncovered requirements.
- **Never hand the plan to an executor before all three validators pass.**

## Reference Docs

| Need                            | Reference                                                      |
| ------------------------------- | -------------------------------------------------------------- |
| Spec sections and templates     | [references/spec-template.md](references/spec-template.md)     |
| Domain-specific worked examples | [references/domain-examples.md](references/domain-examples.md) |
| Plan template and task sizing   | [references/plan-template.md](references/plan-template.md)     |
| Discovery guide                 | [references/discovery.md](references/discovery.md)             |
| Validation checklist            | [references/validation.md](references/validation.md)           |
| Traceability spine details      | [references/traceability.md](references/traceability.md)       |
| Output examples by depth        | [references/output-examples.md](references/output-examples.md) |
