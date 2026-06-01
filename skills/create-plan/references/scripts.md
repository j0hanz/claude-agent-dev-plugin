# Built-In Helper Scripts

These scripts are bundled with the skill. They run automatically during the workflow but can be invoked manually for debugging or standalone use.

---

## discover.py — File & Symbol Discovery

Find files matching a pattern and extract function/class symbols with line numbers.

**Syntax**:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/discover.py \
  --files "src/**/*.ts" \
  --names "generateToken,verifyToken" \
  --json
```

**Output** (`--json`):

```json
{
  "files": [],
  "symbols": [
    {
      "file": "src/utils/jwt.ts",
      "line": 15,
      "match": "export function generateToken(payload: JWTPayload): string {"
    }
  ]
}
```

**When to use**:

- Verifying file paths before writing plan
- Finding exact line numbers for symbols
- Multi-repo projects (run per repo)
- Ensuring symbols exist before referencing them

---

## generate_plan.py — Plan Skeleton Generator

Takes a spec and generates task structure with phases.

**Syntax**:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_plan.py \
  --spec spec.yaml \
  --component auth-middleware \
  --profile atomic
```

**Profiles**: `atomic` (15-40 tasks), `compact` (6-8 phases), `narrative` (runbook)

**Output**: `plan-skeleton-[component]-1.md` with structure:

```markdown
# Phase 1: Setup

## Task 1: Configure Environment

...

## Task 2: Install Dependencies

...
```

**When to use**:

- Generating initial plan structure from spec
- Choosing task granularity (atomic vs compact vs narrative)
- Re-generating plan if scope changes

---

## validate_plan.py — Plan Validation

Check that completed plan follows all conventions.

**Syntax**:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_plan.py \
  plan-feature-auth-middleware-1.md
```

**Checks**:

- All file paths are markdown-linked `[file.ts](path/to/file.ts)`
- All symbols have line anchors `[func](path#L42)`
- Every task has required fields: Depends on, Files, Symbols, Action, Validate, Expected result
- No circular task dependencies (valid DAG)
- All cross-references (TASK-001, PHASE-001) exist and link

**Output**:

```text
✓ 27 tasks validated
✓ All 45 file links valid
✓ No circular dependencies detected
READY FOR EXECUTION
```

**When to use**:

- Before marking plan complete
- Before handing plan to executor
- When importing plans from other sources
