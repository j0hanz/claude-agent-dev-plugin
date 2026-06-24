# workflow-validator

Spec: [workflow-validator.specs.md](workflow-validator.specs.md)

## Goal

Enable automated validation of plugin manifest and YAML/JSON schemas during developer sessions via a declarative skill and a local session lifecycle hook.

## Current Context
- The plugin contains a schema validator script at `bin/validate-plugin.mjs` that can check the `plugin.json` schema and skill files.
- Session lifecycle hooks are managed via `hooks/hooks.json`.
- There are rules in `AGENTS.md` and conventions that skills must have flat YAML frontmatter in `SKILL.md`.

## PHASE-001: Implementation

### TASK-001: Register validation hooks in hooks.json

Depends on: none
Files: [hooks/hooks.json](hooks/hooks.json)
Symbols: none
Satisfies: REQ-001
Action: Register `SessionStart` and `SessionEnd` hooks in `hooks/hooks.json` pointing to `hooks/workflow-validation.sh`.
Validate: `node bin/validate-plugin.mjs`
Expected result: The hook registration passes manifest schema verification.

### TASK-002: Create workflow-validator skill

Depends on: TASK-001
Files: [skills/workflow-validator/SKILL.md](skills/workflow-validator/SKILL.md)
Symbols: none
Satisfies: REQ-002
Action: Create `skills/workflow-validator/SKILL.md` with flat YAML frontmatter (name/description) and body containing detailed guidance for the agent to resolve manifest and schema validation errors.
Validate: `node bin/validate-plugin.mjs`
Expected result: The validation script verifies the new skill is loaded and structurally valid.

### TASK-003: Implement workflow-validation.sh script

Depends on: TASK-002
Files: [hooks/workflow-validation.sh](hooks/workflow-validation.sh)
Symbols: none
Satisfies: REQ-003
Action: Write a Bash-only script `hooks/workflow-validation.sh` that triggers validation by executing `node bin/validate-plugin.mjs`.
Validate: `bash hooks/workflow-validation.sh`
Expected result: Script runs successfully, prints results, and exits with 0 in a clean repo.

### TASK-004: Validate complete plugin structure and formats

Depends on: TASK-003
Files: [skills/workflow-validator/SKILL.md](skills/workflow-validator/SKILL.md)
Symbols: none
Satisfies: REQ-004
Action: Verify skill YAML frontmatter formats and overall plugin layout via the validate script.
Validate: `npm run validate`
Expected result: Entire plugin validation suite reports 100% success.

## PHASE-END: Acceptance

### TASK-005: Final acceptance verification

Depends on: TASK-004
Files: none
Symbols: none
Satisfies: AC-001, AC-002
Action: Verify both acceptance criteria: that the script validates the skill correctly and the hook trigger runs.
Validate: `node bin/validate-plugin.mjs && bash hooks/workflow-validation.sh`
Expected result: Both commands complete successfully with exit code 0.
