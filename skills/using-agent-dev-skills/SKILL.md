---
name: using-agent-dev-skills
description: "Entry-point meta-skill for the agent-dev plugin. Check at session start or when uncertain which skill to use. Routes tasks to the correct agent-dev skill: brainstorming, planning, test-driven-development, diagnose, code-review, refactor, architecture, create-agent, create-hook, skill-builder, github-automation, verification-before-completion, agents-maintainer. Trigger on 'where do I start', 'which skill', 'how does this work', 'let me build a new agent', 'about to open a PR', 'ready to merge', or at the beginning of any new task in this repo."
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

# Using Agent Dev Skills

## Rules

1. Check the routing table **before any action** — including the first one.
2. When a row matches — even partially — invoke that skill. When in doubt, invoke.
3. Before invoking, output one line: `Routing to \`<skill-name>\`: <reason>.`
4. Priority: explicit user instruction → skill → default model behavior.

<EXTREMELY-IMPORTANT>

## Never Rationalize Skipping

Any thought like "this is simple", "I already know this", "just a quick question", or "I need context first" means you are about to skip incorrectly. Skills apply regardless of perceived complexity. Skills tell you how to gather context — check first, always.

</EXTREMELY-IMPORTANT>

---

## Routing Table

| Task signal                                                                        | Skill                            |
| :--------------------------------------------------------------------------------- | :------------------------------- |
| "let's build X", "add feature", ambiguous design, unclear terminology              | `brainstorming`                  |
| "write a spec", "create a plan", "define requirements"                             | `planning`                       |
| Implementing code, writing functions, any non-trivial implementation               | `test-driven-development` ⚠️     |
| "broken", "debug", "why is X failing", unexpected output, production error         | `diagnose`                       |
| "review this", "check for bugs", before opening a PR (not yet open)                | `code-review`                    |
| "clean up", "refactor", "simplify", "hard to read"                                 | `refactor`                       |
| "architecture review", "too coupled", "where should this live", "God class"        | `architecture`                   |
| "add hook", "block a tool", "auto-format", lifecycle guarantees                    | `create-hook`                    |
| "build an agent", "create subagent", "agent prompt", "agent not working"           | `create-agent`                   |
| "make a skill", "build skill", "skill not working", "turn workflow into skill"     | `skill-builder`                  |
| "add CI", "set up release", GitHub Actions, `gh` CLI scripting                     | `github-automation`              |
| PR already open and "ready for review"                                             | `code-review`                    |
| "done", "ready to merge", "looks good" — PR not yet reviewed                       | `verification-before-completion` |
| "update AGENTS.md", "improve agent instructions", "onboard me", trimming CLAUDE.md | `agents-maintainer`              |

> ⚠️ **Agentic skills** (`test-driven-development`, `code-review` execution mode) run autonomously for many tool calls. Before invoking, output: `This will start an autonomous session (~N tool calls). Proceed?` and wait for confirmation. Skip confirmation in subagent context.

---

## Lifecycle Chain

For a complete feature, skills connect in order:

```
brainstorming
     │
     ▼
  planning
     │
     ▼
test-driven-development  ◄── (loop: RED → GREEN → REFACTOR)
     │
     ▼
verification-before-completion
     │
     ▼
  code-review
     │
     ▼
github-automation
```

Side paths — invoke at any stage when the signal matches:

| Signal                                 | Skill                        |
| :------------------------------------- | :--------------------------- |
| Code breaks mid-build                  | `diagnose`                   |
| Code is hard to follow or change       | `architecture` or `refactor` |
| Building a new skill                   | `skill-builder`              |
| Building a new agent or subagent       | `create-agent`               |
| Adding a lifecycle hook                | `create-hook`                |
| Updating project or agent instructions | `agents-maintainer`          |

---

## Skill Types

| Type                                 | Skills                                                                              | Rule                                               |
| :----------------------------------- | :---------------------------------------------------------------------------------- | :------------------------------------------------- |
| **Rigid** — phase gates, no skipping | `test-driven-development`, `diagnose`, `planning`, `verification-before-completion` | Every phase in order. Gates block. Never skip.     |
| **Flexible** — adapt to context      | `brainstorming`, `refactor`, `code-review`, `architecture`                          | Apply judgment within phases. Complete all phases. |

---

## If a Routed Skill Is Missing

Tell the user: `The \`<skill-name>\` skill is not installed. Proceeding without it.`
Then apply the skill's intent manually.

---

## Quick-Start Decision

Stop at the first match:

1. No spec or design → `brainstorming` → `planning`
2. Failing test, crash, unexpected behavior → `diagnose`
3. Implementation done → `verification-before-completion` → `code-review`
4. Building a skill, agent, or hook → `skill-builder` / `create-agent` / `create-hook`
5. Code hard to understand or change → `architecture` or `refactor`
