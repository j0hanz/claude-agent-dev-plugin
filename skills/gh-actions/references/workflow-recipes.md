# Workflow Recipes

Minimal, current templates. Copy the structures from the referenced resource files and customize them to fit your project.

All recipes assume the **three non-negotiables** from SKILL.md:

1. Pin third-party actions to SHA (run `scripts/pin_actions.py` or pin manually before finalizing).
2. Explicit `permissions:` set for least privilege.
3. Untrusted inputs handled via `env:` variables, never directly in `run:` scripts.

## 1. CI Workflow

Standard build and test workflow triggered on push and PR.

- **Recipe file**: [ci.yml](../resources/workflows/ci.yml)
- **Key details**:
  - `concurrency` cancels running jobs on branch push, but is skipped on `main` to preserve deployment.
  - Setup uses Node with native caching configured.
  - For monorepos, use `paths` filters to run checks only on changed packages.

## 2. Release Workflow

Builds artifacts, publishes to GitHub Releases, and creates OIDC provenance on tags.

- **Recipe file**: [release.yml](../resources/workflows/release.yml)
- **Key details**:
  - Permissions set to `contents: write` (release creation) and `id-token: write` (OIDC).
  - Uses standard provenance attestation steps.
  - Recommended OIDC trusted publishers for NPM/PyPI instead of hardcoded tokens.

## 3. Deploy Workflow

Deploys dist artifacts using OIDC credentials for cloud services.

- **Recipe file**: [deploy.yml](../resources/workflows/deploy.yml)
- **Key details**:
  - Defines target `environment: production` to prompt review gates.
  - Job-level `id-token: write` scope (restricted from build/test jobs).
  - Use repository/environment variables (not secrets) for non-sensitive values like ARNs, region, or bucket name.

## 4. Matrix Workflow

Runs tests across node versions and operating systems.

- **Recipe file**: [matrix.yml](../resources/workflows/matrix.yml)
- **Key details**:
  - `fail-fast: false` prevents cancellations of other matrix cells if one fails.
  - Generates matrix dynamically. For complex monorepos, see dynamic matrix expansion at [dynamic_matrix.yml](../resources/workflows/dynamic_matrix.yml).

## 5. Shared Orchestration: Reusable Workflows vs Composite Actions

- **Reusable Workflows**: Shared job-level configuration. Defines its own runner, permissions, and matrix.
  - **Recipe file**: [reusable_workflow.yml](../resources/workflows/reusable_workflow.yml)
- **Composite Actions**: Shared step-level configuration inlined directly into callers.
  - **Recipe file**: [composite_action.yml](../resources/workflows/composite_action.yml)
  - _Must specify `shell:` for every `run:` step. Requires `actions/checkout` before use._

## 6. Scheduled Workflows

- **Trigger syntax**:
  ```yaml
  on:
    schedule:
      - cron: '0 6 * * *' # UTC daily
    workflow_dispatch: # allows manual trigger
  ```
- **Gotchas**: UTC timezone only; runs on the default branch; schedules disabled automatically after 60 days of repo inactivity.
