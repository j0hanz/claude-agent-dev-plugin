---
name: make-a-skill
description: "Guides the scaffolding, authoring, and structural verification of local development skills in the repository. Accepts a target skill name and required subdirectory flags as input, and outputs a complete file template skeleton or a detailed validation check report indicating structural errors. Trigger on: 'make a skill', 'build a skill', 'create a skill', 'scaffold a skill', 'new skill', 'make-a-skill', 'validate this skill', 'lint this skill', 'validate skill structure'. Also triggers when troubleshooting path configurations, resolving leftover placeholders, or checking formatting rules. Always prefer this orchestrator over architecting when creating new instruction files or auditing skill structures."
disable-model-invocation: false
---

# make-a-skill

Scaffold a new skill from a template, draft its body, then validate it before calling it done.

**Entry point:** this skill is reached directly from skill-authoring requests ("make a skill", "validate this skill"), not through `using-agent-dev-skills`'s Gate 0-4 flow — that router operates on the target repo's code, not on the plugin's own `skills/` directory. See `using-agent-dev-skills`'s NEVER list (it routes all skill authoring here).

## Process Flow

```
0. Name Collision Check
  -- exists -------> Exists-Gate (AskUserQuestion)
                       -- Continue ---> 1.5 Pattern Pick
                       -- Overwrite --> 1. Survey + Scaffold (--force)
                       -- Rename -----> back to 0
  -- no collision -> 1. Survey + Scaffold
1. Survey + Scaffold (AskUserQuestion once, then scaffold_skill.py)
  -> 1.5 Pattern Pick (AskUserQuestion)
  -> 2. Draft Body (fill placeholders, leave description)
  -> 3. Validate (validate_skill.py)
       -- errors? yes --> back to 2. Draft Body
       -- errors? no  --> 4. Write Real Description + revalidate -> Done
```

## Step 0: Name Collision Check

Check if `<name>/SKILL.md` exists in either `.claude/skills/<name>` or `skills/<name>`.

- **If it does NOT exist:** Proceed directly to Step 1.
- **If it DOES exist:** Do not touch anything. Prompt via a single `AskUserQuestion`: _"A skill named '' already exists."_ Provide these options:
- **Continue drafting it (Recommended):** Skip Step 1 entirely. Proceed to Step 1.5 using the existing files.
- **Overwrite with fresh template:** Proceed to Step 1, appending the `--force` flag.
- **Pick a different name:** Ask for a new name and restart Step 0.

## Step 1: Resource Survey & Scaffolding

Execute a **single, batched** `AskUserQuestion` call (never split into multiple round-trips):

1. **Resources (Multi-select):** "Which bundled resources does this skill need?" (`scripts/`, `references/`, `evals/`, `none`). Mark the most logical choice based on the task description as "(Recommended)".
2. **Location (Single-select, Conditional):** "Where should this skill live?" (`.claude/skills/` or `skills/`). _Only ask this if ambiguous (both exist or neither exists). If obvious, decide silently and skip this question._

Run the scaffolding script using **only** the exact flags selected in the survey. `<name>` must be lowercase kebab-case.

```bash
python "$CLAUDE_PLUGIN_ROOT/skills/make-a-skill/scripts/scaffold_skill.py" <name> [--scripts] [--references] [--evals] [--dir skills] [--force]

```

## Step 1.5: Select Structural Pattern

Prompt via `AskUserQuestion` (Single-select): _"Which structural pattern fits this skill?"_ Mark the best fit as "(Recommended)".

- **Process:** Phased workflow (~200 lines). _Action: Keep the numbered Process Flow diagram._
- **Tool:** Decision trees for strict formatting (~300 lines).
- **Mindset:** Thinking patterns over technique (~50 lines). _Action: Delete the Process Flow section; body must be short and NEVER heavy._
- **Navigation:** Minimal routing to sub-scenarios (~30 lines). _Action: Body consists mostly of links to sub-files._

## Step 2: Draft the Body

- Fill all `{{FILL: ...}}` placeholders **EXCEPT** `description`. Leave `description` completely untouched.
- Ground each section in concrete procedures. Do not write generic advice.
- If the skill does not require a branching Process Flow diagram, delete that section entirely.

## Step 3: First Validation

Run the validator from the target repository root (not the plugin root):

```bash
python "$CLAUDE_PLUGIN_ROOT/skills/make-a-skill/scripts/validate_skill.py" <name>

```

- **Fix all `[X]` Errors:** Resolve all leftover `{{FILL}}` tags, path mismatches, or dangling links to non-existent files before continuing.
- **Review `[!]` Warnings:** Use judgment to resolve vague adjectives, passive voice, or excessive length.

## Step 4: Finalize Description & Revalidate

1. **Write the Description:** Now replace the `description` placeholder. It must:

- Be written in the third person.
- State exactly what the skill is for.
- Name the alternative sibling skill to use if this one doesn't apply.
- End with an explicit clause: `Trigger on: 'phrase one', 'phrase two'`.

2. **Revalidate:** Re-run the validation script from Step 3.
3. **Confirm:** It MUST return `VALID (0 error(s))`. Zero errors are mandatory.

---

## Critical Constraints

- **NEVER write the description early:** It must be written in Step 4 so it reflects the actual drafted body, not an initial guess.
- **NEVER hand-write the skeleton:** Always use `scaffold_skill.py` to maintain proper `{{FILL}}` placeholder conventions.
- **NEVER guess scaffolding flags:** `--scripts`, `--references`, and `--evals` must strictly match the user's Step 1 survey answers.
- **NEVER expose raw stack traces:** Catch `FileExistsError` during the Step 0 Name Collision Check.
- **NEVER skip repo validation:** If the target repository has its own validator (e.g., `npm run validate`), run it in addition to `validate_skill.py`.

**Next Skills:**

- `eval-skill`: After the skill validates structurally, to behavior-test whether its description actually triggers and it produces the right output.
- `architecting`: Trigger ONLY if structural questions arise during drafting (e.g., circular references or shared logic placement).
- `context-optimizer`: If context bloats mid-skill (long reads, many tool calls).
