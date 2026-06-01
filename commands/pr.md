---
description: Validate the current branch and open a GitHub pull request
argument-hint: [--draft]
---

# Pull Request

Validate all changes on the current branch and create a GitHub pull request following project conventions.

Runs the full validation sequence (tests, lint, AGENTS.md check) before opening the PR.

Current branch: !`git branch --show-current`
Diff from main: !`git diff main...HEAD --stat`
Commits ahead: !`git log main..HEAD --oneline`
Test status: !`npm test 2>&1 | tail -20`

## Usage

- Work is complete and all local tests pass
- AGENTS.md is up to date for any new agents or skills added
- After `/coder` or `/fix` completes and the change is ready to ship

Do not run if tests are failing or uncommitted changes are unintentional — fix those first.

## Execution Steps

1. Run `npm test` — stop and report failures if any
2. Verify AGENTS.md is up to date for any new agents or skills
3. Stage relevant changes: `git add` specific files (not `-A`)
4. Commit with attribution: message + `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
5. Push branch: `git push -u origin <branch>`
6. Create PR via `gh pr create` with Summary (3 bullets) and Test plan sections

## Troubleshooting

**`npm test` fails** — Do not proceed. Fix with `/fix` or `/coder`, then rerun `/pr`.

**`git push` rejected** — Remote has diverged. Run `git pull --rebase origin main`, resolve conflicts, then push.

**`gh pr create` errors with "not authenticated"** — Run `gh auth login`, complete the browser flow, then rerun `/pr`.

**PR already exists for this branch** — Use `gh pr edit` to update the existing PR description instead.

## Success Criteria

- `npm test` passes
- PR URL returned and accessible
- PR title is under 70 characters
- PR body has Summary and Test plan sections
- Branch is pushed and PR is open on GitHub
