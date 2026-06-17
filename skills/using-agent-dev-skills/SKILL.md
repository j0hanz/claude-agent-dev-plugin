---
name: using-agent-dev-skills
description: "Entry-point meta-skill for the agent-dev plugin. Check at session start or when uncertain which skill to use. Routes tasks to the correct agent-dev skill: brainstorming, planning, test-driven-development, multi-agent-development, multi-agent-dispatch, diagnose, code-review, refactor, architecture, create-agent, create-hook, skill-builder, github-automation, verification-before-completion, agents-maintainer. Trigger on 'where do I start', 'which skill', 'how does this work', 'about to open a PR', 'ready to merge', or at the beginning of any new task in this repo."
---

# using-agent-dev-skills

Global entry point for agent-dev plugin coordination. Follow this routing logic for ALL tasks.

## Rules

1. **Check Table First:** Evaluate before any action.
2. **Invoke Immediately:** If a signal matches, route to that skill.
3. **Notify:** Output one line: `Routing to \`<skill-name>\`: <reason>.`
4. **No Skips:** Do NOT skip because a task seems \"simple\" or \"quick\".

## Routing Table

| Signal                                               | Skill                            |
| :--------------------------------------------------- | :------------------------------- |
| \"build X\", \"new feature\", Ambiguous design       | `brainstorming`                  |
| \"write spec\", \"create plan\"                      | `planning`                       |
| Implementation, writing code, functions              | `test-driven-development` ⚠️     |
| \"broken\", \"debug\", Production error, Traceback   | `diagnose`                       |
| \"review this\", Before opening PR                   | `code-review`                    |
| \"clean up\", \"refactor\", \"simplify\"             | `refactor`                       |
| \"architecture review\", \"God class\", Coupled code | `architecture`                   |
| \"add hook\", \"auto-format\", Lifecycle guards      | `create-hook`                    |
| \"build agent\", \"subagent\", Agent prompt error    | `create-agent`                   |
| \"in parallel\", \"fan out\", 2+ independent tasks   | `multi-agent-dispatch`           |
| \"implement plan\", \"build all tasks\"              | `multi-agent-development`        |
| \"make skill\", \"skill not working\"                | `skill-builder`                  |
| \"add CI\", GitHub Actions, `gh` CLI                 | `github-automation`              |
| \"done\", \"ready to merge\"                         | `verification-before-completion` |
| \"update AGENTS.md\", \"onboard me\"                 | `agents-maintainer`              |

⚠️ **Agentic Skill Warning:** `test-driven-development` and `code-review` execute autonomously.
**Confirm:** Output `This will start an autonomous session (~N calls). Proceed?` and wait for user confirmation.

## Lifecycle Chain

```mermaid
graph TD
    A[brainstorming] --> B[planning]
    B --> C1[multi-agent-development]
    B --> C2[test-driven-development]
    B --> C3[multi-agent-dispatch]
    C1 --> D[verification-before-completion]
    C2 --> D
    C3 --> D
    D --> E[code-review]
    E --> F[github-automation]
```

## Quick-Start Gates

1. **No spec?** → `brainstorming` → `planning`
2. **Crash/Failure?** → `diagnose`
3. **Done?** → `verification-before-completion` → `code-review`
4. **Building Meta?** → `skill-builder` | `create-agent` | `create-hook`

## Skip Disclaimer

If a skill is missing: `The \`<skill-name>\` skill is not installed. Proceeding without it.` then apply intent manually.
