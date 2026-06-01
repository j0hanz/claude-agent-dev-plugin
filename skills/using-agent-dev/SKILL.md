---
name: using-agent-dev
description: Use when working on the agent-dev plugin itself — for authoring, testing, validating, or shipping agents, skills, hooks, or documentation. Trigger on 'agent-dev', 'using agent-dev', 'how to use agent-dev'. Always check for relevant skills before acting.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill — your instructions already include full context from the parent session.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, YOU MUST INVOKE IT BEFORE ACTING.

This is not negotiable. Not optional. Invoking a skill that turns out not to apply costs nothing. Skipping a skill that should have applied causes rework.
</EXTREMELY-IMPORTANT>

---

## What Agent-Dev Is

Agent-Dev is a Claude Code plugin for **authoring, testing, validating, and shipping agents, skills, and hooks**. It provides:

- **18 skills** — process and domain methodologies loaded on demand
- **4 managed agents** — scoped subagents for delegated autonomous work
- **8 slash commands** — entry points for common workflows
- **15 lifecycle hooks** — automatic context injection, formatting, and nudges
- **Validation infrastructure** — `npm validate` for plugin health; `npm test` for full test suite

Everything in this repo follows a **skill-first, design-before-code** discipline. The output style enforces four phases: **Design → Build → Validate → Ship**.

---

## Instruction Priority

1. **User's explicit instructions** (CLAUDE.md, AGENTS.md, direct requests) — highest priority
2. **Agent-dev skills** — override default behavior where they conflict
3. **Default system prompt** — lowest priority

---

## Skill-First Rule

**Invoke relevant skills BEFORE any response or action.** Even clarifying questions wait until you have checked for applicable skills.

```
User message → Might any skill apply? → YES → Invoke Skill tool → Follow skill
                                       → DEFINITELY NOT → Respond directly
```

### Red Flags (Stop — You Are Rationalizing)

| Thought                              | Reality                                                  |
| ------------------------------------ | -------------------------------------------------------- |
| "This is just a quick fix"           | Quick fixes become large tasks. Check for skills.        |
| "I need more context first"          | Skills tell you HOW to gather context. Check first.      |
| "Let me look at the code first"      | Skills tell you HOW to explore. Check first.             |
| "I remember this skill"              | Skills evolve. Always read current version.              |
| "The skill is overkill here"         | Simple tasks become complex. Skills prevent wasted work. |
| "I'll just start then use the skill" | Skill check comes BEFORE the first action.               |
| "This doesn't need a formal process" | If a skill exists for it, use it.                        |

### Skill Priority Order

1. **Process skills first** (brainstorming, diagnose, create-plan) — determine HOW to approach
2. **Implementation skills second** (refactor, code-review, tdd) — guide execution

"Let's build X" → `brainstorming` first, then implementation skills.
"Fix this bug" → `diagnose` first, then domain skills.

---

## Skills Index

### Process / Methodology Skills

| Skill                            | Invoke when…                                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------------------------ |
| `brainstorming`                  | Starting any new feature, component, agent, skill, or hook. **Required before design approval.** |
| `create-plan`                    | Translating an approved design into an atomic implementation plan.                               |
| `create-specs`                   | Writing formal specifications for a component before building.                                   |
| `spec-driven-development`        | Full spec-first development lifecycle with validation gates.                                     |
| `test-driven-development`        | Any non-trivial logic that needs red-green-refactor discipline.                                  |
| `skill-builder`                  | Creating, testing, improving, or evaluating a skill.                                             |
| `create-agent`                   | Designing a new managed agent (system prompt, tools, model, context).                            |
| `create-hook`                    | Designing or implementing a lifecycle hook handler.                                              |
| `verification-before-completion` | Final validation sweep before marking work complete or shipping.                                 |
| `architecture`                   | Checking code locality, coupling, or module boundary decisions.                                  |

### Domain / Execution Skills

| Skill         | Invoke when…                                                                                              |
| ------------- | --------------------------------------------------------------------------------------------------------- |
| `code-review` | Reviewing a diff or PR (accepts `--low`, `--medium`, `--high`, `--ultra` effort flags; `--fix` to apply). |
| `refactor`    | Cleaning up code without behavior change. Trigger on "messy", "hard to follow", "simplify".               |
| `diagnose`    | Debugging a failure, tracing a runtime error, or investigating unexpected behavior.                       |
| `diagrams`    | Visualizing architecture, workflows, hook flow, or data models.                                           |
| `research`    | Scoped web research on libraries, APIs, or external services.                                             |

### Lifecycle / Ops Skills

| Skill               | Invoke when…                                                      |
| ------------------- | ----------------------------------------------------------------- |
| `agents-maintainer` | Keeping AGENTS.md and CLAUDE.md in sync after structural changes. |
| `delivery-manager`  | Validating, committing, and opening a PR (invoke via `/deliver`). |

---

## Managed Agents

Delegate to agents for isolated, autonomous work. Each runs in its own context — give it everything it needs in the prompt, because it has no access to the parent session.

### `coder`

- **Job:** Autonomous code execution — implement, refactor, fix, test
- **Isolation:** Git worktree (changes land in a branch, not your working tree)
- **Preloaded skills:** `refactor`, `diagnose`
- **Use when:** A task requires many file edits, a known implementation approach, or you want to protect the main session from churn
- **Invoke:** Mention `@coder` or use the `coder` skill

### `detective`

- **Job:** Root-cause analysis — stack traces, logic bugs, resource leaks
- **Read-only:** Cannot modify files; returns a structured bug report with diff proposals
- **Output format:** Severity / Category / Root cause / Evidence / Proposed fix
- **Use when:** A bug is non-obvious, cross-file, or you want an independent diagnosis
- **Invoke:** Mention `@detective`

### `documenter`

- **Job:** Generate or update AGENTS.md, README, CLAUDE.md, skill docs
- **Use when:** Structure changed, new components added, or docs are stale
- **Invoke:** Mention `@documenter` or `/docs`

### `explorer`

- **Job:** Read-only code search and research (Haiku model — low cost)
- **Use when:** You need to find symbols, trace usage, or research a library before acting
- **Invoke:** Mention `@explorer`

---

## Slash Commands

| Command     | What it does                                                |
| ----------- | ----------------------------------------------------------- |
| `/welcome`  | Session orientation — announces available skills and agents |
| `/plan`     | Invokes `create-plan` skill for current task                |
| `/new`      | Starts a new component with brainstorming + spec workflow   |
| `/check`    | Runs `npm validate` + tests, reports health                 |
| `/deliver`  | Validate → commit (with attribution) → open PR              |
| `/test`     | Runs full test suite (`npm test`)                           |
| `/refactor` | Invokes `refactor` skill on current or specified file       |
| `/docs`     | Invokes `documenter` agent to sync documentation            |

---

## Hook Behaviors (What Fires Automatically)

You do not invoke these — they fire on lifecycle events:

| Trigger                                     | What happens                                                       |
| ------------------------------------------- | ------------------------------------------------------------------ |
| Session start                               | Context injected; skill list announced; explorer state initialized |
| `UserPromptSubmit` on creative/design tasks | Brainstorm-nudge suggests invoking `brainstorming` skill           |
| `PostToolUse` Write/Edit on JS/Python files | Auto-format via ESLint/Prettier (JS) or Ruff (Python)              |
| `PostToolUseFailure` on Bash errors         | Diagnose-nudge surfaces `diagnose` skill and `@detective` agent    |
| `PreToolUse` Glob/Grep/Read                 | Explorer pre-fetches and enriches context                          |
| `Stop` / `SessionEnd`                       | Debug artifact scan; explorer state flushed                        |

---

## Output Style: Phase Discipline

Every work session follows four phases. **Do not skip phases or merge them.**

### Design Phase

- State the component type, trigger condition, and approach in a table **before writing any code**
- Get explicit design approval from the user before proceeding
- `brainstorming` skill governs this phase

### Build Phase

- One-line intent, then act — no preamble
- Every claim about existing code includes a `file:line` citation
- Sequential file edits only — one edit per turn per file

### Validate Phase

- Report as `PASS` or `FAIL`
- Each failure is a triple: **component → rule violated → specific fix**
- Run `npm validate` and `npm test` before marking complete

### Ship Phase

- List artifacts produced and what the next session can build on
- Commit using `/deliver` — never commit without it
- All AI commits MUST include the attribution trailer (see below)

---

## Commit Attribution — Required on Every AI Commit

Every commit made by or with AI assistance MUST include this trailer:

```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Use `/deliver` to handle this automatically. If committing manually, add the trailer via HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
feat: describe what changed

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Tech Stack Quick Reference

- **Runtime:** Node.js ≥ 22 (ESM, no TypeScript — use `.mjs` for hook handlers)
- **Python:** ≥ 3.10, managed via `uv` / `pyproject.toml`
- **Package management:** `npm` (JS), `uv` (Python)
- **Validation:** `npm validate` (plugin health), `npm test` (full suite)
- **Hook dispatch:** `hooks/runner.mjs <domain> <action>` → `hooks/handlers/<domain>.mjs`
- **No logic outside runner pattern** — all hook logic lives in `hooks/handlers/`

---

## Key Paths

| Path                         | Purpose                                        |
| ---------------------------- | ---------------------------------------------- |
| `AGENTS.md`                  | Primary contributor guide — read this first    |
| `skills/<name>/SKILL.md`     | Each skill's instructions and frontmatter      |
| `agents/<name>.md`           | Each managed agent's system prompt and config  |
| `commands/<name>.md`         | Each slash command definition                  |
| `hooks/runner.mjs`           | Central hook dispatcher                        |
| `hooks/hooks.json`           | Event → handler registration                   |
| `hooks/handlers/*.mjs`       | Hook handler modules                           |
| `output-styles/agent-dev.md` | Output style spec (Design/Build/Validate/Ship) |
| `bin/validate-plugin.mjs`    | Plugin validation entrypoint                   |
