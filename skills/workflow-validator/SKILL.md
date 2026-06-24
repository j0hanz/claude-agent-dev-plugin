---
name: workflow-validator
description: "Validates plugin manifests, event hooks, and YAML/JSON schemas for structural compliance and formatting. Trigger on: 'validate plugin', 'validate manifest', 'check schema', 'run validation', 'workflow-validator', 'validate-plugin'."
---

# workflow-validator

Validate the plugin's structural compliance, manifest definitions, schema constraints, and skill formatting.

## Usage

To check the entire plugin's structural compliance and layout:

```bash
node bin/validate-plugin.mjs
```

Or run via npm:

```bash
npm run validate
```

## How to Resolve Failures

When validation fails, review the logs for `[Skill]`, `[Hooks]`, `[Routing]`, or `[Plugin.json]` error messages, and address them as follows:

### 1. YAML Frontmatter Errors (e.g. `Missing YAML frontmatter`, `Invalid line in YAML frontmatter`)
- **Cause:** Every skill file in `skills/<name>/SKILL.md` must start and end with `---` enclosing valid, flat YAML metadata.
- **Resolution:** 
  - Ensure the frontmatter contains only flat key-value pairs (primarily `name` and `description`).
  - Do not use nested structures.
  - Quote values containing colons (e.g. `description: "Triggers on: 'validate'"`).

### 2. Large Skill Warnings (e.g. `Large skill (X lines) should extract content to references/`)
- **Cause:** A skill file exceeds 300 lines.
- **Resolution:** Extract detailed guides, background, or examples into files under a `references/` subdirectory (e.g., `skills/<name>/references/`). Keep `SKILL.md` concise.

### 3. Hook Configuration Errors (e.g. `Command doesn't reference ${CLAUDE_PLUGIN_ROOT}`)
- **Cause:** Hooks registered in `hooks/hooks.json` are invalid, missing their script handler, or contain hardcoded paths.
- **Resolution:**
  - Hook handler commands must be Bash-only and must be wrapped in a `.sh` file inside `hooks/` directory.
  - Reference the plugin root dynamically via `${CLAUDE_PLUGIN_ROOT}` rather than using absolute or relative paths directly.
  - Verify that the target `.sh` file exists under `hooks/`.

### 4. Cross-Skill Routing Errors (e.g. `dangling cross-skill reference`, `Skill 'x' is not referenced in the router`)
- **Cause:** Relative path references (such as `../make-a-skill/`) that point to a non-existent or invalid sibling skill folder exist in skill markdown, or a newly added skill is not wired into the central orchestrator's graph.
- **Resolution:**
  - Verify all relative skill links exist and map to real skill directories.
  - Wire any new skill into the `using-agent-dev-skills` router graph in `skills/using-agent-dev-skills/SKILL.md`.

### 5. Plugin Manifest Errors (e.g. `author must be an object`, `version must be a string`)
- **Cause:** `.claude-plugin/plugin.json` fails structure verification.
- **Resolution:** Match `.claude-plugin/plugin.json` with the required fields: `author` as an object with `name`, `version` as a string, and `keywords` as an array.

### 6. Non-Atomic Requirements (e.g. `Requirement may not be atomic (contains 'and')`)
- **Cause:** Specification requirements (in planning/design specs) are joined with conjunctions like "and", which combines two obligations.
- **Resolution:** Split the requirement into two distinct, atomic requirement IDs (e.g., `REQ-001` and `REQ-002`) so they can be independently validated and satisfied.

## Next Skills
- **using-agent-dev-skills:** Resume orchestrating tasks once validation succeeds.
- **make-a-skill:** Scaffold or modify skill structures.
