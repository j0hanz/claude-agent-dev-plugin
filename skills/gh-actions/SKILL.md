---
name: gh-actions
description: 'Generates, audits, and hardens GitHub Actions workflows and headless gh CLI scripts from user requirements. Use when the user requests "setup CI/CD", "add GitHub Actions", "pin workflows to SHA", "configure OIDC authentication", "harden a workflow", or "write a gh batch/API script". Action: reads current YAML configs and outputs secure, SHA-pinned, least-privilege workflows. Not for committing/branching/opening a PR for an ordinary code change — that is `pr-workflow`.'
---

# gh-actions

Secure, high-performance CI/CD authoring and `gh` CLI automation. This skill is about the _content_ of workflows and batch scripts (hardening, OIDC, pagination), not shipping your day-to-day diff — to branch, commit, and open a PR for a reviewed change, use `pr-workflow`.

## Process Flow

```
Trigger: Workflow/CLI Request
  -- yml / CI --> Path A: ACTIONS
                    -> 1. Classify Intent
                    -> 2. Author & Harden (SHA-pinning/OIDC)
                    -> 3. Validate & Audit (lint/security review)
                         -- runtime fail ---> diagnose (handoff)
                         -- hygiene issue --> refactor (handoff)
  -- gh / API --> Path B: CLI
                    -> 1. Mode Selection (inline vs script)
                    -> 2. Headless Standards (auth/paginate)
                    -> 3. Safety & Idempotency (snapshot/check existence)
                         -- script fail --> diagnose (handoff)
```

## STRICT SECURITY RULES

1. **Block Injections:** NEVER put `${{ github.event... }}` or inputs directly in `run:`. Always pass them through `env:`.
2. **Block Untrusted Code:** NEVER use `pull_request_target` to check out PR code.
3. **Block Permanent Keys:** NEVER save long-lived cloud keys as secrets. Use short-lived OIDC tokens.
4. **Block Secret Leaks:** NEVER use `secrets: inherit` unless you manually check every secret is needed.

## ROUTING

- **Path A (Actions):** For `.yml` workflows, CI, or releases.
- **Path B (CLI):** For `gh` scripts and API tasks.
- _Rule:_ Run scripts from this skill folder. Example: `python3 "<skill_dir>/scripts/script.py path/to/file"`.

## PATH A: ACTIONS (YAML)

1. **Confirm Plan:** Ask the user to pick between: (1) Recommended plan, or (2) Alternative plan.
2. **Read Required Files:** You MUST read `references/workflow-recipes.md`. If deploying to cloud, also read `references/oidc-cloud.md`.
3. **Write Code:**
   - Pin all actions to exact SHA using `python3 scripts/pin_actions.py <path>`.
   - Set default permissions to `contents: read`.
   - Use OIDC (`id-token: write`).
4. **Validate:** Read `references/security-hardening.md`. Run `python3 scripts/lint.py <path>`.
5. **Audit:** Send `references/schemas.md` to the `general-purpose` agent to review security.

## PATH B: CLI (gh)

1. **Confirm Plan:** Ask the user to pick between: (1) Recommended plan, or (2) Alternative plan.
2. **Read Required Files:** You MUST read `references/headless-auth-patterns.md` and `references/api-pagination-and-limits.md`.
3. **Write Script:**
   - Set `GH_PROMPT_DISABLED=1`.
   - Check login first: `gh auth status`.
   - Get clean data: Use `gh api --paginate --jq`.
   - Be safe: Save IDs before editing many things. Add pause times in loops.
   - Do not duplicate: Check if an item exists before creating it.

## SECURITY CHECKLIST (MANDATORY)

- [ ] `permissions` are explicitly set.
- [ ] Third-party actions are SHA-pinned.
- [ ] User inputs use `env:`, never `run:`.
- [ ] Uses OIDC instead of permanent cloud keys.
- [ ] `pull_request_target` is safe.

## NEXT STEPS & ERRORS

- **If anything fails:** Read `references/troubleshooting.md`.
- **`diagnose`:** Call this if a script fails while running.
- **`refactor`:** Call this if the linter or security audit finds bad code.
- **`verification-before-completion`:** Call this to double-check work before saving.
- **`pr-workflow`:** Call this to create a branch, commit, and open a PR.
- **`context-optimizer`:** Call this if the chat memory gets too full.
