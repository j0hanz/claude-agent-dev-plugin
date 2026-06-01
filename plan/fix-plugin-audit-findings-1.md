# Plugin Audit Findings Remediation Plan

## Goal

Resolve all findings from the `claude-plugin-validation` audit of the `agent-dev`
plugin. Six findings were raised: four Warnings (W-1 through W-4) and two Info
items (I-1, I-2). One finding (W-4) was subsequently disproved during discovery
and is documented as a non-issue. The remaining five require code changes.

## Requirements & Constraints

- REQ-001: All 18 `SKILL.md` files must include a `version:` field in YAML frontmatter (W-1)
- REQ-002: Skill `description:` values must not exceed 200 characters; extended trigger
  guidance must move to a body section (W-2)
- REQ-003: Hook events `PostToolUseFailure` and `SessionEnd` in `hooks/hooks.json` must
  be verified as valid Claude Code events; invalid events must be removed or replaced (W-3)
- REQ-004: `package.json` must declare a Node version constraint via the `engines` field (I-2)
- REQ-005: All command files must use `## Usage` as the section header, not `## When to Use` (I-1)
- CON-001: W-2 changes must not reduce skill triggering accuracy — the 200-char description
  must contain the core trigger signal; extended examples move to the body only
- CON-002: Hook event changes in W-3 must preserve existing handler behaviour wherever
  a valid alternative event exists

## Current Context

**Finding W-4 — RESOLVED / NON-ISSUE**
Discovery showed `CLAUDE.md` and `GEMINI.md` are regular 29-byte files containing
`# See [AGENTS.md](AGENTS.md)`. This is a supported Claude Code redirect convention,
not a broken symlink. No action required.

**Skill files** (18 total, all missing `version:` and all with long descriptions):

- [skills/agents-maintainer/SKILL.md](skills/agents-maintainer/SKILL.md)
- [skills/architecture/SKILL.md](skills/architecture/SKILL.md)
- [skills/brainstorming/SKILL.md](skills/brainstorming/SKILL.md)
- [skills/create-agent/SKILL.md](skills/create-agent/SKILL.md)
- [skills/create-hook/SKILL.md](skills/create-hook/SKILL.md)
- [skills/create-plan/SKILL.md](skills/create-plan/SKILL.md)
- [skills/create-specs/SKILL.md](skills/create-specs/SKILL.md)
- [skills/delivery-manager/SKILL.md](skills/delivery-manager/SKILL.md)
- [skills/diagnose/SKILL.md](skills/diagnose/SKILL.md)
- [skills/diagrams/SKILL.md](skills/diagrams/SKILL.md)
- [skills/github-automation/SKILL.md](skills/github-automation/SKILL.md)
- [skills/refactor/SKILL.md](skills/refactor/SKILL.md)
- [skills/research/SKILL.md](skills/research/SKILL.md)
- [skills/skill-builder/SKILL.md](skills/skill-builder/SKILL.md)
- [skills/spec-driven-development/SKILL.md](skills/spec-driven-development/SKILL.md)
- [skills/test-driven-development/SKILL.md](skills/test-driven-development/SKILL.md)
- [skills/using-agent-dev/SKILL.md](skills/using-agent-dev/SKILL.md)
- [skills/verification-before-completion/SKILL.md](skills/verification-before-completion/SKILL.md)

**Command files** (7 total):

- [commands/brainstorm.md](commands/brainstorm.md)
- [commands/coder.md](commands/coder.md)
- [commands/diagram.md](commands/diagram.md)
- [commands/explore.md](commands/explore.md)
- [commands/fix.md](commands/fix.md)
- [commands/hook.md](commands/hook.md)
- [commands/pr.md](commands/pr.md)

**Other files**:

- [package.json](package.json) — missing `engines` field
- [hooks/hooks.json](hooks/hooks.json) — uses `PostToolUseFailure` and `SessionEnd`

---

## Phase 1: Package Config (I-2)

### TASK-001: Add `engines` field to package.json

Depends on: none
Files: [package.json](package.json)
Action: Insert `"engines": { "node": ">=22" }` as a top-level field after `"private": true`.
Validate: `node -e "const p=JSON.parse(require('fs').readFileSync('package.json','utf8')); console.assert(p.engines && p.engines.node,'missing'); console.log('ok')"`
Expected result: Prints `ok`, exits 0

---

## Phase 2: Hook Event Verification (W-3)

### TASK-002: Audit valid Claude Code hook event names

Depends on: none
Files: [hooks/hooks.json](hooks/hooks.json)
Action: Read the Claude Code hooks documentation to confirm which event names are
supported. Cross-reference the six events currently in `hooks.json`:
`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
`PostToolUseFailure`, `Stop`, `SessionEnd`.
Document the result (supported / unsupported) as a comment block at the top of
`hooks/hooks.json` using a `_docs` key, OR proceed directly to TASK-003.
Validate: Read `hooks/hooks.json` and confirm all event key names are in the
verified-supported list.
Expected result: Each event key name is confirmed valid or flagged for removal.

### TASK-003: Remove or replace unsupported hook events

Depends on: [TASK-002](#task-002-audit-valid-claude-code-hook-event-names)
Files: [hooks/hooks.json](hooks/hooks.json)
Action: For each event found unsupported in TASK-002:

- If `PostToolUseFailure` is unsupported: remove the `PostToolUseFailure` block.
  Add a comment in `hooks/hooks.json` (`"_note_diagnose-nudge"`) explaining the
  handler exists but cannot fire — the `diagnose-nudge` handler becomes manual-only.
- If `SessionEnd` is unsupported: remove the `SessionEnd` block. The `explorer flush`
  handler already runs async; loss of this event means breadcrumb flushing only
  occurs on the next `SessionStart` replay instead.
- If both are supported: make no changes; update TASK-002 comment to record that.
  Validate: `node -e "const h=JSON.parse(require('fs').readFileSync('hooks/hooks.json','utf8')); const keys=Object.keys(h.hooks); console.log(keys.join(', '))"`
  Expected result: Only verified-valid event names appear in the output.

---

## Phase 3: Command File Headers (I-1)

### TASK-004: Rename `## When to Use` → `## Usage` in command files

Depends on: none
Files: all 7 files in [commands/](commands/)
Action: In each command `.md` file, rename the section header `## When to Use` to
`## Usage`. If a file already uses `## Usage` or has no such section, skip it.
Validate: `node -e "const fs=require('fs'),path=require('path'); const dir='commands'; fs.readdirSync(dir).filter(f=>f.endsWith('.md')).forEach(f=>{const t=fs.readFileSync(path.join(dir,f),'utf8'); if(t.includes('## When to Use')) console.log('STILL HAS OLD HEADER:',f);}); console.log('done')"`
Expected result: Prints only `done` — no files still carry the old header.

---

## Phase 4: Skill Version Field (W-1)

### TASK-005: Add `version: 1.0.0` to all 18 SKILL.md frontmatter blocks

Depends on: none
Files: all 18 `skills/*/SKILL.md` files listed in Current Context
Action: In each SKILL.md, insert `version: 1.0.0` as the last line of the YAML
frontmatter block (before the closing `---`). The frontmatter currently ends with
the `description:` block scalar; append `version: 1.0.0` after it.
Validate: `node -e "const fs=require('fs'),path=require('path'); const skills=fs.readdirSync('skills'); let missing=[]; skills.forEach(s=>{const f=path.join('skills',s,'SKILL.md'); if(!fs.existsSync(f))return; const t=fs.readFileSync(f,'utf8'); const fm=t.split('---')[1]||''; if(!fm.includes('version:'))missing.push(s);}); if(missing.length){console.log('MISSING version:',missing.join(', '));process.exit(1);}else console.log('All 18 skills have version field')"`
Expected result: Prints `All 18 skills have version field`, exits 0

---

## Phase 5: Skill Description Condensing (W-2)

**Strategy**: Each skill's `description:` block scalar must be restructured so the
value is ≤200 characters. The condensed description keeps the core trigger signal
(the sentence that answers "when should this skill fire?"). All extended trigger
examples, skip conditions, and detailed guidance move into the skill body under a
new `## When to Apply` section (or an existing equivalent). This preserves
triggering accuracy while meeting the spec guideline.

**Pattern to apply to each skill**:

```yaml
# BEFORE
description: |
  Long multiline description with trigger examples,
  skip conditions, edge cases...

# AFTER
description: One concise sentence ≤200 chars that captures the trigger signal.
```

Then in the body, add or expand:

```markdown
## When to Apply

<former extended description content>
```

### TASK-006: Condense `brainstorming` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/brainstorming/SKILL.md](skills/brainstorming/SKILL.md)
Action: Replace the multi-paragraph `description:` block with a single line ≤200 chars.
Suggested condensed description (153 chars):
`Structured requirements discovery before implementation. Use when building new features, design is ambiguous, or terminology is unclear. Skip for pure bug fixes.`
Move extended trigger guidance into the existing `## Conversation Rhythm` section
or a new `## When to Apply` section above it.
Validate: `node -e "const t=require('fs').readFileSync('skills/brainstorming/SKILL.md','utf8'); const desc=t.match(/^description: (.+)$/m)?.[1]||t.match(/description: \|[\s\S]*?(?=\n\w|\n---)/m)?.[0]||''; console.log('len approx check — first line:'); console.log(t.split('\n').find(l=>l.startsWith('description:')))"`
Expected result: The `description:` line is a single inline value, not a block scalar (`|`).

### TASK-007: Condense `diagnose` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/diagnose/SKILL.md](skills/diagnose/SKILL.md)
Action: Same strategy as TASK-006. Read current description, extract core trigger
signal into ≤200-char single-line value, move extended content to body.
Validate: `node -e "const t=require('fs').readFileSync('skills/diagnose/SKILL.md','utf8'); const line=t.split('\n').find(l=>l.startsWith('description:')); console.log(line); console.assert(!line.includes('|') || line.trim()==='description: |' && false, 'still block scalar')"`
Expected result: `description:` is not a block scalar (`|`).

### TASK-008: Condense `test-driven-development` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/test-driven-development/SKILL.md](skills/test-driven-development/SKILL.md)
Action: Same pattern as TASK-006/007. Core signal: "Write failing test first, then make it pass. Use for any new logic, functions, or modules. Hard-gate: no implementation without a failing test."
Validate: Same pattern — confirm `description:` line is not a block scalar.
Expected result: Single-line description, block content moved to body.

### TASK-009: Condense `spec-driven-development` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/spec-driven-development/SKILL.md](skills/spec-driven-development/SKILL.md)
Action: Same pattern. Core signal captures the mandatory spec-first workflow.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-010: Condense `create-agent` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/create-agent/SKILL.md](skills/create-agent/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-011: Condense `create-hook` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/create-hook/SKILL.md](skills/create-hook/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-012: Condense `create-plan` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/create-plan/SKILL.md](skills/create-plan/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-013: Condense `create-specs` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/create-specs/SKILL.md](skills/create-specs/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-014: Condense `skill-builder` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/skill-builder/SKILL.md](skills/skill-builder/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-015: Condense `architecture` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/architecture/SKILL.md](skills/architecture/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-016: Condense `diagrams` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/diagrams/SKILL.md](skills/diagrams/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-017: Condense `refactor` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/refactor/SKILL.md](skills/refactor/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-018: Condense `research` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/research/SKILL.md](skills/research/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-019: Condense `agents-maintainer` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/agents-maintainer/SKILL.md](skills/agents-maintainer/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-020: Condense `delivery-manager` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/delivery-manager/SKILL.md](skills/delivery-manager/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-021: Condense `github-automation` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/github-automation/SKILL.md](skills/github-automation/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-022: Condense `using-agent-dev` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/using-agent-dev/SKILL.md](skills/using-agent-dev/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

### TASK-023: Condense `verification-before-completion` skill description

Depends on: [TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks)
Files: [skills/verification-before-completion/SKILL.md](skills/verification-before-completion/SKILL.md)
Action: Same pattern.
Validate: Same pattern.
Expected result: Single-line description.

---

## Phase 6: Final Validation

### TASK-024: Run full validation sweep

Depends on: [TASK-001](#task-001-add-engines-field-to-packagejson),
[TASK-003](#task-003-remove-or-replace-unsupported-hook-events),
[TASK-004](#task-004-rename--when-to-use---usage-in-command-files),
[TASK-005](#task-005-add-version-100-to-all-18-skillmd-frontmatter-blocks),
[TASK-023](#task-023-condense-verification-before-completion-skill-description)
Files: all modified files
Action: Run the integration test suite to confirm plugin loads cleanly after all changes.
Validate: `npm run test:integration`
Expected result: Both integration tests pass (`test-skills-load.mjs` confirms all 18
skills load; `test-hooks-fire.mjs` confirms hooks fire without errors). Exit code 0.

---

## Acceptance Criteria

- [ ] `package.json` contains `"engines": { "node": ">=22" }`
- [ ] All hook event names in `hooks/hooks.json` are verified valid Claude Code events
- [ ] No command file contains `## When to Use` — all use `## Usage`
- [ ] All 18 `SKILL.md` files have `version: 1.0.0` in frontmatter
- [ ] All 18 `SKILL.md` `description:` values are single-line strings ≤200 characters
- [ ] `npm run test:integration` exits 0

## Rollback Strategy

All changes are file edits in a git repository. If any phase degrades triggering
accuracy or breaks the integration tests, revert via `git checkout -- <file>`. The
W-2 changes (description condensing) carry the highest risk of reducing triggering
accuracy and can be reverted independently of the other phases if needed.
