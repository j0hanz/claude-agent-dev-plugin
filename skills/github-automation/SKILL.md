---
name: github-automation
description: "Expert authoring and hardening of GitHub Actions and CLI scripts. Master of OIDC, least-privilege permissions, and SHA-pinning. Trigger on 'add CI', 'setup release', 'harden workflow', 'gh api'."
disable-model-invocation: true
allowed-tools: Bash(python *) Bash(python3 *)
---

# github-automation

Secure, high-performance GitHub automation.

## Routing Logic

| Signal                                                    | Path                |
| :-------------------------------------------------------- | :------------------ |
| `.github/workflows/*.yml`, \"add CI\", \"set up release\" | **Path A: ACTIONS** |
| `gh` script, batch API, headless automation               | **Path B: CLI**     |

## PATH A — ACTIONS: YAML Workflows

1. **Classify Intent:** Map to recipe (CI, Release, Deploy, Matrix, Reuse).
2. **Author with Hardening (Non-Negotiable):**
   - **SHA-Pinning:** Replace `@v4` with `@<full_sha>`. Use `pin_actions.py`.
   - **Permissions:** Default to `contents: read`. Widen only where needed.
   - **Injection Prevention:** NEVER interpolate `${{ github.event... }}` into `run:`. Use `env:`.
   - **OIDC:** Use `id-token: write` and cloud OIDC actions instead of long-lived secrets.
3. **Validate:** Run `scripts/lint.py`. Report linter tier (actionlint | python-lint).
4. **Audit:** Dispatch `general-purpose` subagent for semantic security review.

## PATH B — CLI: GitHub CLI Automation

1. **Mode Selection:** One-off command (inline) vs. Headless script (file).
2. **Headless Standards:**
   - Set `GH_PROMPT_DISABLED=1`.
   - Verify auth via `gh auth status` before mutation.
   - Use `gh api --paginate` with `--jq` for structured output.
3. **Safety:** Snapshot IDs before batch mutations. Add jitter/sleep for write loops.
4. **Idempotency:** Check existence before `POST`; prefer `PATCH`.

## Mandatory Security Checklist

- [ ] `permissions:` set explicitly (no reliance on defaults).
- [ ] All third-party actions pinned to 40-char SHA.
- [ ] Untrusted inputs piped through `env:`, never `run:` interpolation.
- [ ] No long-lived cloud credentials (OIDC only).
- [ ] `pull_request_target` audited for PR head checkout (Forbidden).

## Transition

1. **Fail:** Invoke `diagnose` or `refactor` based on blocking issue type.
