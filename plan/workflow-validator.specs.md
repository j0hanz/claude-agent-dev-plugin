# workflow-validator

## 1. Goal

- One sentence: Enable automated validation of plugin manifest and YAML/JSON schemas during developer sessions via a declarative skill and a local session lifecycle hook.
- Completion signal: The validation hook runs successfully on session start/end, and the new skill is loaded and validated by `node bin/validate-plugin.mjs`.

## 2. Requirements

- `REQ-001`: The system MUST support automated validation on session start/end events via a Bash-only hook.
- `REQ-002`: The system MUST provide detailed validation instructions within `skills/workflow-validator/SKILL.md` to guide the agent on resolving errors.
- `REQ-003`: The hook script MUST execute `node bin/validate-plugin.mjs` to run the validation code.
- `REQ-004`: The `skills/workflow-validator/SKILL.md` file MUST contain a valid flat YAML frontmatter with `name`/`description` keys.

## 3. Constraints

- `CON-001`: The hook handler MUST NOT execute Node.js/Python code directly from the hook configuration; it must run via the Bash script `hooks/workflow-validation.sh`.
- `CON-002`: The implementation MUST NOT introduce any new third-party npm package dependencies beyond those already declared in `package.json`.

## 4. Interfaces

The system exposes the following interfaces:

### hooks/workflow-validation.sh

**Input:**
- Event environment variables provided by Claude Code session events.

**Output:**
- Outputs validation results to stdout/stderr.

**Errors:**
- Exit 1: Validation failed (if schema or manifest is invalid).
- Exit 0: Validation succeeded.

### hooks/hooks.json

**Input:**
- Configuration mapping `SessionStart` and `SessionEnd` events to the Bash-only script `hooks/workflow-validation.sh`.

**Output:**
- JSON manifest format mapping event names to script paths.

**Errors:**
- Validation failure if schema does not match plugin manifest validator.

## 5. Context

- Files:
  - [hooks/hooks.json](file:///C:/agent-dev/hooks/hooks.json)
  - [bin/validate-plugin.mjs](file:///C:/agent-dev/bin/validate-plugin.mjs)
  - [package.json](file:///C:/agent-dev/package.json)
- Current behavior:
  - There is a `validate-plugin.mjs` script in `bin/` that validates `plugin.json` schema and skill files.
  - Currently, validation is only run manually via `npm run validate` or `npm test`.
- Conventions:
  - Hook scripts are located in `hooks/` and must be Bash-only.
  - Skills are located in `skills/` and must have `SKILL.md` with flat YAML frontmatter.

## 6. Acceptance Criteria & Validation

- `AC-001`: Running `node bin/validate-plugin.mjs` completes with success after adding the new skill.
- `VAL-001`: `node bin/validate-plugin.mjs`
- `AC-002`: The hook script `hooks/workflow-validation.sh` runs and executes successfully.
- `VAL-002`: `bash hooks/workflow-validation.sh`

## 7. Examples & Edge Cases

**Positive example:**
```
Input: Run bash hooks/workflow-validation.sh in a clean, valid repository.
Output: Validation output confirms all manifest and skill checks pass. Exit code 0.
```

**Edge cases:**
- Invalid plugin manifest (e.g. missing fields): The hook reports the errors and exits with a non-zero code.
- Missing SKILL.md in `skills/workflow-validator/`: The hook reports that the new skill is invalid and exits with code 1.
