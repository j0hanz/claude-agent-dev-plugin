# Design Spec: project-init Monorepo Directory-Scoped Merges

This design document outlines the support for generating package-level, directory-scoped `AGENTS.md` files in monorepos using the `project-init` skill.

---

## 1. Overview & Objectives

AI coding agents function best when they are not overwhelmed with bloated instruction files. In a monorepo, a single root `AGENTS.md` containing rules for every individual package violates the instruction budget. 

This design establishes a clean separation of concerns:
1. **Root `AGENTS.md`**: Contains the global "Hard Rules" (commit policy, testing policy, CI config, attribution) and a high-level overview of the repository/workspace.
2. **Package-level `AGENTS.md`**: Placed at each package root (e.g., `packages/api/AGENTS.md`). Contains package-scoped stack details, custom developer conventions, and file-scoped commands. Inherits global rules and excludes duplicate sections to optimize token budgets.

---

## 2. CLI & Technical Changes in `init.py`

### 2.1 CLI Flags
Add a `--package` parameter to the `generate` command:

```python
gen.add_argument(
    "--package",
    default=None,
    help="Relative path to package directory (e.g. 'packages/api'). If set, generates a package-scoped AGENTS.md."
)
```

### 2.2 Claim Filtering Logic
When `--package <rel_path>` is provided, `init.py` filters the unified JSON claims array by checking if the cited evidence paths reside inside the specified subdirectory:

```python
# Normalize to forward slashes with a trailing slash for prefix checking
prefix = rel_path.strip().replace(os.sep, "/").rstrip("/") + "/"

# Filter claims: evidence path must start with the package prefix
filtered_winners = {
    k: claim for k, claim in winners.items()
    if claim.evidence.path.replace(os.sep, "/").startswith(prefix)
}
```

### 2.3 Output Generation Logic
When `--package` is active:
1. **Header**: Render H1 as `# Agent Instructions: <package_path>`.
2. **Hard Rules Omitted**: Exclude the global `## Hard Rules` section.
3. **Commit Attribution Omitted**: Exclude the global `## Commit Attribution` and `Co-Authored-By` sections.
4. **Identifier Marker**: Write the comment block `<!-- project-init:package-scoped <package_path> -->` instead of `<!-- project-init:hard-rules ... -->`.

---

## 3. Linter Updates in `init.py`

`init.py lint` must validate package-level `AGENTS.md` files without requiring root-level rules.

1. **Marker Detection**:
   ```python
   _PKG_MARKER_RE = re.compile(r"<!--\s*project-init:package-scoped\s+(\S+)\s*-->")
   is_package_scoped = bool(_PKG_MARKER_RE.search(content))
   ```
2. **Conditional Assertions**:
   - If `is_package_scoped` is `True`:
     - Skip the check for `## Hard Rules`.
     - Skip the check for `## Commit Attribution` / `Co-Authored-By:`.
     - Skip the check for the global `project-init:hard-rules` marker.
     - Validate that the `project-init:package-scoped` marker is present.
   - Else (root level):
     - Perform all standard validations (H1, Hard Rules, Marker, Commit Attribution, and Attribution trailer).
   - Both modes still lint for budget limits (`MAX_LINES`), unresolved placeholders (`TODO`, `<Model Name>`), and filler text.

---

## 4. SKILL.md Orchestration Changes

We will update [SKILL.md](file:///C:/agent-dev/skills/project-init/SKILL.md) to explain the monorepo workflow.

### Phase 2: Check and Preview
- Read the prescan JSON.
- If `is_monorepo` is true:
  - Generate and preview root `AGENTS.md`: `python init.py generate --claims claims.json --commit <c> --maturity <m> --testing <t> --ci <ci>`
  - For each path `p` in `packages`:
    - Generate and preview package-scoped draft: `python init.py generate --claims claims.json --package p --commit <c> --maturity <m> --testing <t> --ci <ci>`

### Phase 3: Consent + Write
- If root `AGENTS.md` or any `<package_path>/AGENTS.md` already exists, request consent before overwriting.
- Write root: `python init.py generate --claims claims.json ... --model "<model>" --out AGENTS.md`
- For each path `p` in `packages`:
  - Write package-scoped file: `python init.py generate --claims claims.json --package p --model "<model>" --out p/AGENTS.md`
- Wire redirect stubs at root: `python init.py wire AGENTS.md CLAUDE.md GEMINI.md`
- Lint all generated files:
  - `python init.py lint AGENTS.md`
  - For each `p` in `packages`: `python init.py lint p/AGENTS.md`

---

## 5. Verification & Test Plan

1. **Unit Tests in `test_init.py`**:
   - Verify filtering logic resolves package prefixes correctly.
   - Verify generated package `AGENTS.md` does not write Hard Rules or Attribution.
   - Verify linter passes package-scoped files with the correct marker and fails if required structures are missing.
2. **Integration Verification**:
   - Setup a dummy workspace with a root and two sub-packages (`packages/pkg-a`, `packages/pkg-b`).
   - Run `generate` commands for root and packages. Verify files are created at correct paths and successfully pass the `lint` command.
