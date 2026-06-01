# Skill Patterns & Design Guide

Best practices and patterns for authoring skills in the agent-dev plugin.

## Overview

Skills in agent-dev follow a **progressive disclosure** model:

1. **Frontmatter** — Loaded at startup (triggers, metadata)
2. **Body** — Core guidance (50-150 lines)
3. **References** — Detailed examples (lazy-loaded on demand)

This structure keeps context concise while supporting unbounded knowledge.

## Skill Structure

### Directory Layout

```text
skills/skill-name/
├── SKILL.md           # Frontmatter + core guidance
├── references/        # Optional: detailed docs
│   ├── api-guide.md
│   ├── examples/
│   │   ├── example-1.md
│   │   └── example-2.md
│   └── troubleshooting.md
├── scripts/           # Optional: automation scripts
│   ├── helper.mjs
│   └── helper.test.mjs
├── agents/            # Optional: skill-specific agents
│   └── reviewer.md
└── evals/             # Optional: evaluation cases
    └── test-cases.yaml
```

### SKILL.md Template

```markdown
---
name: skill-name
description: When to activate this skill. Triggers: "phrase A", "phrase B", "phrase C". Also covers: general topics.
---

# Skill Name

[50-150 line core guidance with examples and workflow]

## Additional Resources

- **API Reference**: [`references/api-guide.md`](references/api-guide.md)
- **Troubleshooting**: [`references/troubleshooting.md`](references/troubleshooting.md)
- **Examples**: [`references/examples/`](references/examples/)
```

## Frontmatter Specification

### Required Fields

| Field         | Type   | Example                                     | Purpose                                        |
| ------------- | ------ | ------------------------------------------- | ---------------------------------------------- |
| `name`        | string | `"test-driven-development"`                 | Unique identifier (kebab-case)                 |
| `description` | string | `"When to use TDD, trigger phrases, scope"` | 1-2 sentences; triggers are activation signals |

### Optional Fields

| Field                      | Type    | Example            | Purpose                                               |
| -------------------------- | ------- | ------------------ | ----------------------------------------------------- |
| `disable-model-invocation` | boolean | `false`            | Prevent Claude invocation (for reference-only skills) |
| `allowed-tools`            | string  | `"Bash(npm *)"`    | Restrict tool access (`*` = any arg)                  |
| `user-invocable`           | boolean | `true`             | Callable via `/` command                              |
| `argument-hint`            | string  | `"[--flag] <arg>"` | CLI usage hint                                        |

### Example Frontmatter

```yaml
---
name: architecture
description: "Use when reviewing system design, identifying circular deps, or designing new systems. Triggers: 'architecture review', 'God class', 'too coupled'."
disable-model-invocation: false
allowed-tools: Bash(node *)
user-invocable: true
argument-hint: '[--fix] [--explain]'
---
```

## Body Content Patterns

### Pattern 1: Routing

For skills with multiple paths, start with a routing table:

```markdown
# Skill Name

Use this skill for [domain]. Choose one path:

| Signal        | Path        |
| ------------- | ----------- |
| User says "X" | Path A: ... |
| User says "Y" | Path B: ... |

---

## PATH A: First approach

[Detailed guidance for path A]

---

## PATH B: Second approach

[Detailed guidance for path B]
```

**Example**: `skills/github-automation/SKILL.md` (Actions vs. gh CLI)

### Pattern 2: Sequential Workflow

For skills with a clear step-by-step process:

```markdown
# Skill Name

## Workflow (5 Steps)

| Step | Action                  | Gate                                  |
| ---- | ----------------------- | ------------------------------------- |
| 1    | Understand requirements | Are requirements clear?               |
| 2    | Design the solution     | Does design address all requirements? |
| 3    | Implement               | Does code match design?               |
| 4    | Test                    | Do tests pass?                        |
| 5    | Document                | Is documentation complete?            |

### Step 1: Understand Requirements

[Detailed guidance]

### Step 2: Design the Solution

[Detailed guidance]

...
```

**Example**: `skills/create-plan/SKILL.md` (5 core steps)

### Pattern 3: Anti-Patterns

For skills focused on correctness, show what NOT to do:

```markdown
## Anti-Pattern 1: [Name]

❌ **WRONG**:
```

code example

```

Why this breaks: explanation

✅ **RIGHT**:
```

correct example

```

Why this works: explanation
```

**Example**: `skills/create-plan/SKILL.md` (Anti-patterns section)

## Progressive Disclosure Patterns

### When to Move Content to References

Move content to `references/` if:

1. **Body exceeds 200 lines** — Split into body + `references/`
2. **Contains detailed API docs** — Move to `references/api.md`
3. **Contains many code examples** — Move to `references/examples/`
4. **Contains troubleshooting steps** — Move to `references/troubleshooting.md`
5. **Contains decision matrices** — Move to `references/decisions.md`

### Reference Naming Convention

| Content Type    | Filename                             | Purpose                             |
| --------------- | ------------------------------------ | ----------------------------------- |
| Detailed API    | `api-guide.md` or `api-reference.md` | Comprehensive API reference         |
| Code examples   | `examples/example-name.md`           | Concrete, runnable examples         |
| Troubleshooting | `troubleshooting.md`                 | Common issues and fixes             |
| Decision matrix | `decisions.md` or `patterns.md`      | Comparison tables                   |
| Scripts         | `scripts/` dir                       | Helper scripts (separate from docs) |
| Advanced topics | `advanced.md`                        | Deep dives for expert users         |

### Linking to References

In SKILL.md body:

```markdown
For detailed API reference, see [`references/api-guide.md`](references/api-guide.md).

For examples, see [`references/examples/`](references/examples/).
```

**Example**: `skills/create-plan/SKILL.md` uses reference links throughout.

## Trigger Phrases

Good trigger phrases are:

- **Specific**: "add JWT auth" not just "auth"
- **Action-oriented**: "fix failing test" not "something is wrong"
- **Scope-limited**: "refactor this function" not "improve code"
- **Phrased as user would say them**: "I need a plan" not "instantiate planning module"

### Trigger Phrase Examples

```
✅ GOOD: "add form validation", "refactor the database layer", "fix circular dependency"
❌ BAD: "auth", "tests", "refactoring" (too vague)

✅ GOOD: "add integration tests", "why is this test failing", "set up CI workflow"
❌ BAD: "tests", "CI", "testing" (too generic)
```

## Skill Integration Points

### As a Slash Command

Add to `commands/` to expose via `/slash`:

```markdown
---
description: What this command does
argument-hint: <arg>
---

# Command Name

Invokes the skill via `/command-name <args>`.
```

### As an Agent Skill

Reference from agent frontmatter:

```yaml
skills:
  - name: skill-name
  - name: another-skill
```

When the agent runs, these skills are injected into its context.

### As a Hook Handler

Skills can include helper scripts used by hooks:

```
skills/skill-name/scripts/
├── helper.mjs        # Used by hooks/handlers/domain.mjs
└── helper.test.mjs   # Test for helper
```

## Testing Skills

### Evaluation Cases (evals/)

Create YAML files with test cases:

```yaml
# skills/skill-name/evals/test-cases.yaml

- input: 'trigger phrase'
  expected_activation: true
  expected_output_contains:
    - 'keyword from body'
    - 'specific guidance'

- input: 'wrong phrase'
  expected_activation: false
```

Run evaluation:

```bash
python skills/skill-builder/tests/eval.py skills/skill-name/evals/test-cases.yaml
```

### Unit Tests for Scripts

For `scripts/` helpers, use Node tests:

```bash
node --test skills/skill-name/scripts/helper.test.mjs
```

## Skill Examples from Codebase

### Example 1: create-plan (Large Skill with References)

- **Body size**: 393 lines (well-structured, not overwhelming)
- **References**: 7 detailed docs (`discovery.md`, `template.md`, `validation.md`, etc.)
- **Pattern**: Sequential workflow + anti-patterns + reference links
- **Why it works**: Body is readable; details are in references

**Structure**:

```
✓ SKILL.md: Core workflow (5 steps), key concepts, anti-patterns
✓ references/template.md: Plan template with examples
✓ references/discovery.md: File/symbol discovery detailed guide
✓ references/validation.md: Validation checklist
```

### Example 2: github-automation (Routed Skill)

- **Body size**: 279 lines (dual-path routing)
- **References**: 7 specialized docs (Actions, CLI, security, troubleshooting)
- **Pattern**: Dual routing (PATH A vs PATH B) with intent classification
- **Why it works**: Clear routing prevents user from following the wrong path

**Structure**:

```
✓ SKILL.md: Router table + PATH A + PATH B
✓ references/workflow-recipes.md: Action workflow recipes
✓ references/security-hardening.md: Security best practices
```

### Example 3: brainstorming (Small Skill)

- **Body size**: 159 lines (focused)
- **References**: None (keep body compact, no need for references)
- **Pattern**: Sequential with clear scope
- **Why it works**: Fits in one focused document

**Structure**:

```
✓ SKILL.md: When to apply, workflow, examples
✓ No references: Not needed; body is self-contained
```

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Trigger Phrases Too Vague

```yaml
description: 'Use this skill for development' # BAD: Too vague
```

**Why it breaks**: Overlaps with everything; won't trigger reliably.

**Fix**: Make triggers specific to a workflow:

```yaml
description: "Structured requirements discovery before implementation. Trigger on 'let's build', 'add a feature', 'design this system'."
```

### ❌ Anti-Pattern 2: Body Over 400 Lines Without References

**Why it breaks**: Too much context; harder to find specific guidance.

**Fix**: Move detailed examples and advanced topics to `references/`:

```
SKILL.md: 150-200 lines (core workflow)
references/examples/: Detailed examples
references/advanced.md: Deep dives
```

### ❌ Anti-Pattern 3: Frontmatter Without Description

```yaml
---
name: skill-name
---
```

**Why it breaks**: Skill won't load; missing trigger information.

**Fix**: Always include `description`:

```yaml
---
name: skill-name
description: 'When to use this, trigger phrases, scope.'
---
```

### ❌ Anti-Pattern 4: Mixing Multiple Topics

```markdown
# My Skill

How to do testing, how to do debugging, how to do documentation...
```

**Why it breaks**: Users don't know which path to follow; triggers are unclear.

**Fix**: Focus on one domain or use routing:

```markdown
# My Skill

Choose one: Testing? Debugging? Documentation?

## PATH A: Testing

## PATH B: Debugging

## PATH C: Documentation
```

## Checklist: Before Committing a Skill

- [ ] `SKILL.md` exists and has YAML frontmatter
- [ ] `description` field is specific and includes trigger phrases
- [ ] Body is 50-300 lines (content > 300 lines? split to references/)
- [ ] Links to references use markdown format: `[text](path/to/ref.md)`
- [ ] No hardcoded file paths (use `${CLAUDE_SKILL_DIR}` or relative paths)
- [ ] Code examples are tested or marked `# pseudocode`
- [ ] References folder is organized by topic
- [ ] Scripts have unit tests if in `scripts/` directory
- [ ] Evaluation cases exist if skill has multiple activation paths
- [ ] Skill is mentioned in `AGENTS.md` if relevant to plugin architecture

## Maintenance

### Keeping Skills Up-to-Date

1. **Check triggers quarterly** — Do trigger phrases still match user language?
2. **Validate code examples** — Run scripts to ensure they still work
3. **Update references** — Add new examples, remove deprecated patterns
4. **Link cross-skills** — If Skill A refers to Skill B, add that reference

### Deprecating a Skill

To retire a skill:

1. Rename `SKILL.md` → `SKILL.deprecated.md`
2. Update `AGENTS.md` with deprecation note
3. Link to replacement skill in deprecation message
4. Keep the file for 1-2 releases for backward compatibility

## References

- **Validation**: Run `npm validate` to check all skills
- **Testing**: Run `npm test` to run all skill tests
- **Viewing**: Skills are loaded by Claude Code; inspect via `/check all`
