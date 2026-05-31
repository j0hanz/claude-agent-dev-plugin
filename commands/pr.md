---
description: Validate the current branch and open a GitHub pull request
argument-hint: [--draft]
---

# Pull Request

Validate all changes on the current branch and create a GitHub pull request following project conventions.

Runs the full validation sequence (tests, lint, AGENTS.md check) before opening the PR. Uses the deliver skill for commit attribution and the GitHub CLI for the PR.

Current branch: !`git branch --show-current`
Diff from main: !`git diff main...HEAD --stat`
Commits ahead: !`git log main..HEAD --oneline`
Test status: !`npm test 2>&1 | tail -20`

## When to Use

- Work is complete on the current branch and ready for review
- All local tests pass and AGENTS.md is up to date for any new agents or skills
- You want a consistent PR format (Summary + Test plan) without writing it manually
- After `/coder` or `/fix` completes a task and the change is ready to ship

Do not run if tests are failing or uncommitted changes are unintentional — fix those first.

## Execution Steps

1. Run `npm test` — if any tests fail, stop and report failures
2. Check AGENTS.md is up to date for any new agents or skills added
3. Stage all relevant changes: `git add` specific files (not -A)
4. Commit with attribution: message summarizing the change + "Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
5. Push branch: `git push -u origin <branch>`
6. Create PR via `gh pr create` with Summary (3 bullets) and Test plan sections

## Troubleshooting

**`npm test` fails** — Do not proceed. Fix the failures with `/fix` or `/coder`, then rerun `/pr`.

**`git push` rejected** — The remote may have diverged. Run `git pull --rebase origin main`, resolve conflicts, then push again.

**`gh pr create` errors with "not authenticated"** — Run `gh auth login` and complete the browser flow. Rerun `/pr` once authenticated.

**PR already exists for this branch** — `gh pr create` will fail. Use `gh pr edit` to update the existing PR description instead.

## Success Criteria

- `npm test` passes
- PR URL returned and accessible
- PR description covers what changed and why
- PR title is under 70 characters
- PR body has Summary and Test plan sections
- Branch is pushed and PR is open on GitHub

Open the PR URL and confirm the description reads clearly before requesting review.
