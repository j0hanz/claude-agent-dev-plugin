#!/usr/bin/env python3
"""
Consolidated health check script for the agent-sdlc plugin.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import IO, Any, ClassVar


class Config:
    """Central configuration for plugin audit utilities."""

    # ── Dependency directory names → display label ─────────────────────────
    DEPENDENCY_DIRS: ClassVar[dict[str, str]] = {
        "node_modules": "Node.js (npm/pnpm/yarn/bun)",
        "venv": "Python (virtualenv)",
        ".venv": "Python (virtualenv)",
        "env": "Python (virtualenv)",
        ".env": "Python (virtualenv)",
        "__pypackages__": "Python (PEP 582)",
        ".direnv": "direnv",
        ".conda": "Conda environment",
        "vendor": "PHP (Composer) / Go (vendoring)",
        "Pods": "iOS (CocoaPods)",
        "target": "Rust (Cargo)",
        "dist": "Build output",
        "build": "Build output",
        ".next": "Next.js build",
        "out": "Build output",
        "bin": "Executables / scripts",
        "lib": "Shared libraries / dependencies",
        "extern": "External dependencies",
    }

    # ── Lock file → package manager name ───────────────────────────────────
    PACKAGE_MANAGERS: ClassVar[dict[str, str]] = {
        "pnpm-lock.yaml": "pnpm",
        "yarn.lock": "yarn",
        "package-lock.json": "npm",
        "bun.lockb": "bun",
        "uv.lock": "uv",
        "poetry.lock": "poetry",
        "Cargo.lock": "cargo",
        "go.sum": "go",
    }

    # ── Default gitignore-style patterns always applied ────────────────────
    DEFAULT_IGNORE_PATTERNS: ClassVar[set[str]] = {
        ".git",
        ".vscode",
        ".idea",
        ".env",
        "*.log",
        "__pycache__",
        ".pytest_cache",
        ".DS_Store",
    }

    # ── AGENTS.md validation constants ─────────────────────────────────────
    MAX_AGENTS_MD_LINES: ClassVar[int] = 100

    # ── Per-language scaffold defaults for `scaffold-agents-md` ───────────
    # Each entry supplies a *starting point* only — the LLM must override any
    # value Phase 1 discovered to differ from the default (e.g. a repo using
    # npm instead of pnpm).
    #
    # "commands" and "conventions" are lists of (label, value) 2-tuples.
    # Both elements are always strings; extend the tuple definition AND all
    # consumers in render_agents_md_skeleton() together if a third element
    # is ever needed.
    LANGUAGE_DEFAULTS: ClassVar[dict[str, dict[str, Any]]] = {
        "node": {
            "pm": "pnpm",
            "toolchain": {
                "install": "pnpm install",
                "dev": "pnpm dev",
                "test": "pnpm test",
            },
            "dependency_locations": {"node_modules": "node_modules/"},
            "commands": [
                ("Typecheck", "pnpm tsc --noEmit path/to/file.ts"),
                ("Lint", "pnpm eslint path/to/file.ts"),
                ("Test", "pnpm jest path/to/file.test.ts"),
            ],
            "conventions": [
                ("imports", "ESM import/export syntax only — no CommonJS require()"),
                (
                    "types",
                    "strict TypeScript types for all function signatures — no implicit or explicit any",
                ),
                (
                    "async-errors",
                    "use async/await with try-catch blocks for asynchronous operations — avoid raw promises",
                ),
            ],
        },
        "python": {
            "pm": "uv",
            "toolchain": {
                "sync": "uv sync",
                "test": "uv run pytest",
                "add-dep": "uv add <pkg>",
            },
            "dependency_locations": {
                "venv": ".venv/",
                "site-packages": ".venv/lib/python3.x/site-packages/",
            },
            "commands": [
                ("Typecheck", "uv run mypy path/to/file.py"),
                ("Lint", "uv run ruff check path/to/file.py"),
                ("Test", "uv run pytest path/to/test_file.py::test_name"),
            ],
            "conventions": [
                (
                    "typing",
                    "use Type Annotations (PEP 484) on all public function definitions",
                ),
                (
                    "style",
                    "follow PEP 8 styling with black formatter — ruff check is the source of truth",
                ),
                (
                    "dependencies",
                    "manage dependencies strictly in pyproject.toml — never run pip directly",
                ),
            ],
        },
        "go": {
            "pm": "Go Modules",
            "toolchain": {
                "tidy": "go mod tidy",
                "build": "go build",
                "test": "go test",
            },
            "dependency_locations": {
                "vendor": "vendor/ (if used)",
                "module-cache": "$GOPATH/pkg/mod",
            },
            "commands": [
                ("Lint", "golangci-lint run path/to/file.go"),
                ("Test", "go test -run TestName path/to/package"),
            ],
            "conventions": [
                (
                    "error-handling",
                    "explicitly handle every returned error immediately — do not ignore with _",
                ),
                (
                    "struct-tags",
                    'use camelCase for JSON tags on public structs (e.g. json:"camelCase")',
                ),
                (
                    "context",
                    "pass context.Context as the first argument to all network and database functions",
                ),
            ],
        },
        "rust": {
            "pm": "Cargo",
            "toolchain": {
                "build": "cargo build",
                "test": "cargo test",
                "lint": "cargo clippy",
            },
            "dependency_locations": {"build-artifacts": "target/"},
            "commands": [
                ("Lint", "cargo clippy --package <pkg_name> -- -D warnings"),
                ("Test", "cargo test --package <pkg_name> test_name"),
            ],
            "conventions": [
                (
                    "error-handling",
                    "use Result<T, E> and the ? operator for propagation — avoid unwrap() and expect()",
                ),
                (
                    "lifetimes",
                    "prefer owned types (String, Vec) in structs to avoid complex lifetime annotations unless performance-critical",
                ),
                (
                    "clippy",
                    "ensure code compiles cleanly with cargo clippy warnings treated as errors",
                ),
            ],
        },
        "java": {
            "pm": "Maven or Gradle",
            "toolchain": {
                "maven-build": "mvn clean install",
                "maven-test": "mvn test",
                "gradle-build": "gradle build",
                "gradle-test": "gradle test",
            },
            "dependency_locations": {
                "maven": "build in target/, cache in ~/.m2/repository",
                "gradle": "build in build/, cache in ~/.gradle",
            },
            "commands": [
                (
                    "Compile",
                    "mvn compile -pl :<module_name> (or gradle -p :<module> build)",
                ),
                ("Test", "mvn test -Dtest=TestClass#testMethod -pl :<module>"),
            ],
            "conventions": [
                (
                    "null-safety",
                    "use Optional<T> for return types that can be empty — never return null",
                ),
                (
                    "dependency-injection",
                    "use constructor injection only — avoid field injection with @Autowired or @Inject",
                ),
                (
                    "naming",
                    "follow standard camelCase for variables/methods and PascalCase for classes",
                ),
            ],
        },
        "dotnet": {
            "pm": "dotnet",
            "toolchain": {
                "restore": "dotnet restore",
                "build": "dotnet build",
                "test": "dotnet test",
            },
            "dependency_locations": {
                "nuget-cache": "~/.nuget/packages",
                "build": "bin/, obj/",
            },
            "commands": [
                ("Build", "dotnet build -p :<ProjectName>"),
                ("Test", "dotnet test --filter FullyQualifiedName~TestClassName"),
            ],
            "conventions": [
                (
                    "async-await",
                    "append the Async suffix to all asynchronous method names and await them",
                ),
                (
                    "null-safety",
                    "enable nullable reference types (<Nullable>enable</Nullable>) and resolve all compiler warnings",
                ),
                (
                    "naming",
                    "use PascalCase for public properties/methods and camelCase for private fields with _ prefix",
                ),
            ],
        },
        "bun": {
            "pm": "bun",
            "toolchain": {
                "install": "bun install",
                "run": "bun run",
                "test": "bun test",
            },
            "dependency_locations": {"modules": "node_modules/"},
            "commands": [
                ("Test", "bun test path/to/file.test.ts"),
                ("Run", "bun path/to/file.ts"),
            ],
            "conventions": [
                (
                    "imports",
                    "ESM import/export syntax for files and packages — no CommonJS require()",
                ),
                (
                    "jsx",
                    "use .tsx or .jsx file extensions for components; never put JSX in .ts or .js files",
                ),
                (
                    "apis",
                    "prefer native Bun APIs (e.g. Bun.serve, Bun.file) over Node.js compat equivalents",
                ),
            ],
        },
    }

    # ── Survey answers → Hard Rules sentence ───────────────────────────────
    # Keys must match the marker value encoding in references/hard-rules.md.
    HARD_RULES_TEXT: ClassVar[dict[str, dict[str, str]]] = {
        "commit": {
            "strict": "Conventional Commits format (`type(scope): subject`) required; every AI commit MUST include a `Co-Authored-By:` trailer",
            "relaxed": "free-form commit messages allowed; every AI commit MUST include a `Co-Authored-By:` trailer",
            "minimal": "no enforced message format, no required attribution trailer",
        },
        "maturity": {
            "production": "stability first — avoid breaking changes, prefer additive changes, flag breaking changes explicitly before making them",
            "development": "breaking changes are fine — never add fallback/legacy-compat shims, rewrite to the better approach directly",
        },
        "testing": {
            "always": "every change must have passing tests before being called done",
            "touched-files": "test/typecheck files you changed; don't require full-suite runs",
            "not-enforced": "no automatic testing requirement, rely on existing CI",
        },
        "ci": {
            "github-actions": "automated CI running on GitHub Actions",
            "gitlab-ci": "automated CI running on GitLab CI",
            "local-only": "no automated CI, local-only test execution and deployment",
        },
    }


class IssueLevel(Enum):
    """Levels for validation issues."""

    WARN = auto()
    FAIL = auto()


@dataclass
class ValidationIssue:
    """Represents a single validation issue or warning."""

    level: IssueLevel
    message: str
    line_number: int | None = None

    def __str__(self) -> str:
        line_info = f" (line {self.line_number})" if self.line_number else ""
        return f"{self.message}{line_info}"


@dataclass
class ValidationResult:
    """Consolidated result of a validation check."""

    success: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.level == IssueLevel.FAIL for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.level == IssueLevel.WARN for issue in self.issues)


@dataclass
class ProjectEnvironment:
    """DTO for the project environment."""

    package_manager: str = "Unknown"
    test_runner: str = "Unknown"
    linter: str = "Unknown"
    is_monorepo: bool = False
    ci_provider: str = "Unknown"


@dataclass
class DependencyInfo:
    """DTO for found dependencies."""

    name: str
    type: str
    path: str


def safe_print(text: str, file: IO[str] = sys.stdout) -> None:
    """Print text safely, handling encoding issues."""
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        # FIX S-6/C-4: capture codec once to avoid a race between two separate
        # getattr() calls, which could diverge when stdout/stderr use different
        # encodings (e.g. cp1252 vs utf-8 on Windows).
        codec = getattr(file, "encoding", None) or "ascii"
        print(text.encode(codec, "replace").decode(codec), file=file)


def load_gitignore(target_dir: Path) -> set[str]:
    """Load ignore patterns from .gitignore file."""
    patterns: set[str] = set()
    try:
        content = (target_dir / ".gitignore").read_text(encoding="utf-8-sig")
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.add(line.rstrip("/"))
    except (OSError, UnicodeDecodeError):
        pass
    return patterns


def should_ignore(path: Path, patterns: set[str], root: Path) -> bool:
    """Check if a path should be ignored based on patterns."""
    try:
        rel_path = path.relative_to(root)
    except ValueError:
        return False

    rel_str = str(rel_path).replace("\\", "/")
    for pattern in patterns:
        is_anchored = pattern.startswith("/")
        # FIX B-7: normalise trailing slash once here so all comparisons below
        # are consistent, even for patterns that bypass load_gitignore (which
        # strips trailing slashes).  Previously the strip was applied only at
        # some of the comparison sites, leaving a latent double-slash bug when
        # a caller passed a pattern with a trailing slash directly.
        pat_clean = (pattern[1:] if is_anchored else pattern).rstrip("/")

        # 1. Unanchored literal or wildcard matching on path name
        if not is_anchored and "/" not in pat_clean:
            if "*" in pat_clean or "?" in pat_clean:
                if fnmatch.fnmatchcase(path.name, pat_clean):
                    return True
            elif path.name == pat_clean:
                return True
            continue

        # 2. Anchored literal match relative to root
        if rel_str == pat_clean or rel_str.startswith(pat_clean + "/"):
            return True

        # 3. Anchored wildcard match relative to root
        if "*" in pat_clean or "?" in pat_clean:
            # Convert glob to regex where '*' matches anything except '/'
            # and '**' matches anything including '/'
            parts = pat_clean.split("**")
            regex_parts = []
            for part in parts:
                escaped = re.escape(part).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
                regex_parts.append(escaped)
            regex_str = "^" + ".*".join(regex_parts) + "(?:/|$)"
            if re.match(regex_str, rel_str):
                return True

    return False


def _parse_frontmatter(content: str) -> dict[str, str]:
    """Simple parser for YAML frontmatter.

    Only flat ``key: scalar`` pairs are supported. Multi-line values,
    lists, and nested mappings are silently ignored or misinterpreted.
    Use a proper YAML parser for richer frontmatter structures.
    """
    content = content.lstrip("\ufeff").lstrip()
    if not content.startswith("---"):
        return {}
    # FIX B-1: use a line-anchored regex so that a YAML scalar value
    # containing the four-character sequence "\n---" does not prematurely
    # terminate the frontmatter block.  The closing delimiter must appear
    # on its own line (optionally followed by whitespace).
    m = re.search(r"\n---\s*(\n|$)", content[3:])
    if m is None:
        return {}
    end = m.start() + 3
    yaml_text = content[3:end]
    result: dict[str, str] = {}
    for line in yaml_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def get_tree_lines(
    target_dir: Path, patterns: set[str], max_depth: int = 3
) -> list[str]:
    """Generate directory tree lines without printing."""
    lines: list[str] = []
    use_unicode = True
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "└".encode(encoding)
    except (UnicodeEncodeError, LookupError):
        use_unicode = False

    branch_last = "└── " if use_unicode else "+-- "
    branch_mid = "├── " if use_unicode else "|-- "
    spacer_last = "    "
    spacer_mid = "│   " if use_unicode else "|   "

    def build_tree(path: Path, prefix: str = "", depth: int = 0) -> None:
        if depth >= max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except OSError:
            return

        non_ignored = [
            entry for entry in entries if not should_ignore(entry, patterns, target_dir)
        ]

        for i, entry in enumerate(non_ignored):
            is_last = i == len(non_ignored) - 1
            current = branch_last if is_last else branch_mid
            extension = spacer_last if is_last else spacer_mid

            if entry.is_dir():
                lines.append(f"{prefix}{current}{entry.name}/")
                build_tree(entry, prefix + extension, depth + 1)
            else:
                lines.append(f"{prefix}{current}{entry.name}")

    build_tree(target_dir)
    return lines


def analyze_project_env(target_dir: Path) -> ProjectEnvironment:
    """Analyze the project environment files."""
    env = ProjectEnvironment()
    try:
        files = {entry.name for entry in target_dir.iterdir() if entry.is_file()}
    except OSError:
        return env

    for lockfile, pm in Config.PACKAGE_MANAGERS.items():
        if lockfile in files:
            env.package_manager = pm
            break

    if any(name.startswith("jest.config") for name in files):
        env.test_runner = "jest"
    elif any(name.startswith("vitest.config") for name in files):
        env.test_runner = "vitest"
    elif "pytest.ini" in files:
        env.test_runner = "pytest"

    if any(name.startswith(".eslintrc") for name in files):
        env.linter = "eslint"
    elif "biome.json" in files:
        env.linter = "biome"
    elif "ruff.toml" in files:
        env.linter = "ruff"

    monorepo_markers = {"turbo.json", "pnpm-workspace.yaml", "nx.json", "lerna.json"}
    if any(name in files for name in monorepo_markers):
        env.is_monorepo = True

    package_json = target_dir / "package.json"
    if package_json.exists():
        try:
            pkg: dict[str, Any] = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})
            if isinstance(scripts, dict):
                if env.test_runner == "Unknown" and scripts.get("test"):
                    env.test_runner = "See package.json test script"
                if env.linter == "Unknown" and scripts.get("lint"):
                    env.linter = "See package.json lint script"
        except (json.JSONDecodeError, OSError):
            pass

    if ".gitlab-ci.yml" in files:
        env.ci_provider = "gitlab-ci"
    else:
        github_workflows = target_dir / ".github" / "workflows"
        if github_workflows.is_dir():
            # FIX B-3: a PermissionError on iterdir() means the directory
            # exists but is unreadable.  Assume GitHub Actions rather than
            # incorrectly labelling the repo as "local-only", which would
            # cause scaffold-agents-md to emit a wrong ci: value.
            try:
                has_files = any(entry.is_file() for entry in github_workflows.iterdir())
                env.ci_provider = "github-actions" if has_files else "local-only"
            except OSError:
                env.ci_provider = "github-actions"
        else:
            env.ci_provider = "local-only"

    return env


def get_dependencies(target_dir: Path) -> list[DependencyInfo]:
    """Find and measure installed dependencies."""
    found: list[DependencyInfo] = []

    try:
        dirs = [e for e in target_dir.iterdir() if e.is_dir()]
    except OSError:
        return found

    for entry in dirs:
        if entry.name in Config.DEPENDENCY_DIRS:
            found.append(
                DependencyInfo(
                    name=entry.name,
                    type=Config.DEPENDENCY_DIRS[entry.name],
                    path=str(entry.relative_to(target_dir)),
                )
            )

    return found


# ── Compiled regular expressions ──────────────────────────────────────────
_FILLER_RE = re.compile(
    r"(welcome to|this document explains|you should)", re.IGNORECASE
)
_AUTO_DISCOVERY_RE = re.compile(
    r"(\d+\s+(tools|resources|prompts)|MCP server)", re.IGNORECASE
)
_GENERIC_ADVICE_RE = re.compile(
    r"\b(always|be sure|remember|carefully|thoroughly|best practice|make sure|important|test thoroughly|be careful)\b",
    re.IGNORECASE,
)
_FILE_SCOPED_COMMANDS_RE = re.compile(r"##\s+file-scoped commands", re.IGNORECASE)
_HARD_RULES_MARKER_RE = re.compile(
    r"<!--\s*codebase-init:hard-rules\s+v1\s+commit=\S+\s+maturity=\S+\s+testing=\S+(?:\s+ci=\S+)?\s*-->"
)
_TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
# FIX C-2: moved here from ~106 lines below to join the consolidated group.
_HARD_RULES_SECTION_RE = re.compile(r"^##\s+Hard Rules\b", re.IGNORECASE | re.MULTILINE)
_PACKAGE_OVERRIDE_RE = re.compile(r"See\s+\[AGENTS\.md\]", re.IGNORECASE)


def render_hard_rules_marker(
    commit: str, maturity: str, testing: str, ci: str | None = None
) -> str:
    """Render the trailing hard-rules marker comment encoding the 3 or 4 survey answers."""
    if ci is not None:
        return f"<!-- codebase-init:hard-rules v1 commit={commit} maturity={maturity} testing={testing} ci={ci} -->"
    return f"<!-- codebase-init:hard-rules v1 commit={commit} maturity={maturity} testing={testing} -->"


def has_hard_rules_marker(content: str) -> bool:
    """Return True if content contains a valid v1 hard-rules marker comment."""
    return bool(_HARD_RULES_MARKER_RE.search(content))


def render_agents_md_skeleton(
    language: str,
    purpose: str,
    commit: str,
    maturity: str,
    testing: str,
    ci: str | None = None,
    pm_override: str | None = None,
    toolchain_overrides: dict[str, str] | None = None,
) -> str:
    """Render a markdown-kv AGENTS.md skeleton with Hard Rules first.

    `pm_override`/`toolchain_overrides` carry real commands discovered in Phase 1 —
    they replace the per-language defaults, which exist only as a starting point and
    must never be hallucinated as fact for a specific repo.
    """
    if language not in Config.LANGUAGE_DEFAULTS:
        raise ValueError(
            f"Unknown language {language!r}. Choices: {sorted(Config.LANGUAGE_DEFAULTS)}"
        )
    categories = [
        ("commit", commit),
        ("maturity", maturity),
        ("testing", testing),
    ]
    if ci is not None:
        categories.append(("ci", ci))

    for category, value in categories:
        if value not in Config.HARD_RULES_TEXT[category]:
            raise ValueError(
                f"Unknown {category} {value!r}. Choices: {sorted(Config.HARD_RULES_TEXT[category])}"
            )

    defaults = Config.LANGUAGE_DEFAULTS[language]
    pm = pm_override or defaults["pm"]
    toolchain = dict(defaults["toolchain"])
    toolchain.update(toolchain_overrides or {})

    lines: list[str] = [
        "# Agent Instructions",
        "",
        f"purpose: {purpose}",
        "",
        "## Hard Rules",
        "",
        f"commit: {Config.HARD_RULES_TEXT['commit'][commit]}",
        f"maturity: {Config.HARD_RULES_TEXT['maturity'][maturity]}",
        f"testing: {Config.HARD_RULES_TEXT['testing'][testing]}",
    ]
    if ci is not None:
        lines.append(f"ci: {Config.HARD_RULES_TEXT['ci'][ci]}")
    lines += [
        "",
        render_hard_rules_marker(commit, maturity, testing, ci),
        "",
        "## Package Manager",
        "",
        f"pm: {pm}",
    ]
    for key, value in toolchain.items():
        lines.append(f"{key}: `{value}`")

    lines += ["", "## Dependency Locations", ""]
    for key, value in defaults["dependency_locations"].items():
        lines.append(f"{key}: `{value}`")

    lines += ["", "## File-Scoped Commands", "", "| Task | Command |", "| --- | --- |"]
    for task, command in defaults["commands"]:
        lines.append(f"| {task} | `{command}` |")

    lines += [
        "",
        "## Key Conventions",
        "",
    ]
    for key, value in defaults["conventions"]:
        lines.append(f"{key}: {value}")

    lines += [
        "",
        "## Commit Attribution",
        "",
        "Co-Authored-By: <Model Name>",
        "",
    ]
    return "\n".join(lines)


def is_package_level_override(content: str) -> bool:
    """Return True if content is a recognized package-level AGENTS.md override."""
    return bool(_PACKAGE_OVERRIDE_RE.search(content))


def _lint_agents_md_lines(lines: list[str], issues: list[ValidationIssue]) -> None:
    """Scan AGENTS.md lines to flag TODOs, filler words, auto-discovered lists, and generic advice."""
    in_code_block = False
    in_html_comment = False
    for index, line in enumerate(lines):
        line_num = index + 1
        line_strip = line.strip()

        if line_strip.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Check for unresolved TODO (always run on non-code-block lines, even comments)
        if _TODO_RE.search(line):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message=f'Unresolved TODO detected: "{line_strip}"',
                    line_number=line_num,
                )
            )

        if in_html_comment:
            if "-->" in line:
                in_html_comment = False
            continue
        if line_strip.startswith("<!--"):
            if "-->" not in line_strip:
                in_html_comment = True
            continue

        # Skip the marker comment itself
        if _HARD_RULES_MARKER_RE.search(line):
            continue

        if _FILLER_RE.search(line):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message=f'Filler text detected: "{line_strip}"',
                    line_number=line_num,
                )
            )
        if _AUTO_DISCOVERY_RE.search(line):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL,
                    message=f'Auto-discovered list detected: "{line_strip}"',
                    line_number=line_num,
                )
            )
        if _GENERIC_ADVICE_RE.search(line):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.WARN,
                    message=f'Generic advice detected: "{line_strip}"',
                    line_number=line_num,
                )
            )


def _validate_agents_md_structure(
    content: str, has_hard_rules_section: bool, issues: list[ValidationIssue]
) -> None:
    """Verify presence of Co-Authored-By, File-scoped commands, and Hard Rules section/marker."""
    if "Co-Authored-By:" not in content:
        issues.append(
            ValidationIssue(
                level=IssueLevel.FAIL,
                message='Missing "Co-Authored-By:" attribution.',
            )
        )
    elif "<Model Name>" in content:
        issues.append(
            ValidationIssue(
                level=IssueLevel.FAIL,
                message='Unresolved "<Model Name>" placeholder: substitute the active model name.',
            )
        )

    if (
        not _FILE_SCOPED_COMMANDS_RE.search(content)
        and "| Tool | File | Command |" not in content
    ):
        issues.append(
            ValidationIssue(
                level=IssueLevel.FAIL,
                message='Missing mandatory "File-scoped commands" table.',
            )
        )

    if not has_hard_rules_section and not is_package_level_override(content):
        issues.append(
            ValidationIssue(
                level=IssueLevel.FAIL,
                message='Missing mandatory "## Hard Rules" section.',
            )
        )
    elif has_hard_rules_section:
        if not has_hard_rules_marker(content):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.WARN,
                    message='"## Hard Rules" section present but missing/malformed '
                    "codebase-init:hard-rules v1 marker comment.",
                )
            )
        else:
            marker_match = _HARD_RULES_MARKER_RE.search(content)
            if marker_match:
                if "ci=" not in marker_match.group(0):
                    issues.append(
                        ValidationIssue(
                            level=IssueLevel.WARN,
                            message="Hard-rules marker comment is missing the 'ci' parameter.",
                        )
                    )


def validate_agents_md_file(file_path: Path) -> ValidationResult:
    """Validate the AGENTS.md file."""
    if not file_path.exists():
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    level=IssueLevel.FAIL, message=f"File not found at {file_path}"
                )
            ],
        )

    issues: list[ValidationIssue] = []
    try:
        content = file_path.read_text(encoding="utf-8").lstrip("\ufeff")
        lines = content.splitlines()

        # FIX C-9: demote line-count to WARN — the limit is advisory; structural
        # failures (missing H1, missing Hard Rules section) should dominate.
        if len(lines) > Config.MAX_AGENTS_MD_LINES:
            issues.append(
                ValidationIssue(
                    level=IssueLevel.WARN,
                    message=f"File is {len(lines)} lines. Recommended maximum is {Config.MAX_AGENTS_MD_LINES}.",
                )
            )

        if not lines or not lines[0].startswith("# "):
            issues.append(
                ValidationIssue(
                    level=IssueLevel.FAIL, message="File must start with an H1 header."
                )
            )

        _lint_agents_md_lines(lines, issues)

        has_hard_rules_section = bool(_HARD_RULES_SECTION_RE.search(content))
        _validate_agents_md_structure(content, has_hard_rules_section, issues)

    except (OSError, UnicodeDecodeError) as e:
        issues.append(
            ValidationIssue(
                level=IssueLevel.FAIL, message=f"Failed to read {file_path}: {e}"
            )
        )

    return ValidationResult(
        success=not any(i.level == IssueLevel.FAIL for i in issues), issues=issues
    )


def wire_agents_files(source: Path, targets: list[Path]) -> int:
    """Create one-line redirect stubs (never full copies) in target files pointing to *source*.

    Each *target* file will contain a markdown link to the *source* file
    using a relative POSIX path. Existing files are overwritten. Returns
    ``0`` on success or ``1`` if any target could not be processed.

    Both *source* and all *targets* must reside inside the current working
    directory. Paths that escape the project root are rejected to prevent
    write-anywhere exploitation and path-traversal link injection (S-2, S-5).
    """
    safe_root = Path.cwd().resolve()
    source = source.resolve()

    # FIX S-2/S-5: reject source outside project root to prevent the generated
    # relative link from containing deep ../../.. traversal sequences.
    if not source.is_relative_to(safe_root):
        safe_print(
            f"FAIL: source is outside the project root: {source.name}",
            file=sys.stderr,
        )
        return 1
    if not source.exists():
        safe_print(f"FAIL: Source file not found: {source.name}", file=sys.stderr)
        return 1

    exit_code = 0
    for target in targets:
        # FIX B-9: use a separate variable for the resolved path to avoid
        # shadowing the original user-supplied value used in error messages.
        resolved_target = target.resolve()

        # FIX S-2: reject targets outside the project root.
        if not resolved_target.is_relative_to(safe_root):
            safe_print(
                f"FAIL: target is outside the project root, skipping: {target}",
                file=sys.stderr,
            )
            exit_code = 1
            continue
        if resolved_target == source:
            safe_print(
                f"FAIL: target is the same file as source, skipping: {target}",
                file=sys.stderr,
            )
            exit_code = 1
            continue
        try:
            target_abs = target.absolute()
            if target_abs.is_dir() and not target_abs.is_symlink():
                raise IsADirectoryError(f"target is a directory: {target_abs}")
            if target_abs.exists() or target_abs.is_symlink():
                target_abs.unlink()
            rel = os.path.relpath(source, target_abs.parent).replace(os.sep, "/")
            target_abs.parent.mkdir(parents=True, exist_ok=True)
            target_abs.write_text(
                f"# See [{source.name}]({rel})\n", encoding="utf-8", newline="\n"
            )
            safe_print(f"Stubbed: {target_abs.name} -> {rel}")
        except (OSError, ValueError) as e:
            safe_print(f"FAIL: Could not wire {target}: {e}", file=sys.stderr)
            exit_code = 1

    return exit_code


def print_validation_issues(result: ValidationResult) -> None:
    """Print validation issues with appropriate levels."""
    for issue in result.issues:
        if issue.level == IssueLevel.FAIL:
            prefix = "FAIL"
        elif issue.level == IssueLevel.WARN:
            prefix = "WARN"
        else:
            prefix = "INFO"
        safe_print(f"{prefix}: {issue}", file=sys.stderr)


def _resolve_target(raw: Path | None, fallback: Path) -> Path:
    """Resolve an optional target_dir argument, falling back to cwd."""
    return (raw or fallback).resolve()


def _print_env(env: ProjectEnvironment) -> None:
    safe_print(f"Package Manager: {env.package_manager}")
    safe_print(f"Test Runner:     {env.test_runner}")
    safe_print(f"Linter:          {env.linter}")
    safe_print(f"Monorepo:        {env.is_monorepo}")
    safe_print(f"CI/CD Automation: {env.ci_provider}")


def _print_dependencies(deps: list[DependencyInfo]) -> None:
    if not deps:
        safe_print("None found.")
        return
    for dep in deps:
        safe_print(f"{dep.name} ({dep.type}) -> {dep.path}")


# ── Subcommand handlers ────────────────────────────────────────────────────
# FIX C-3: non-trivial subcommand bodies extracted into named handler
# functions so they can be unit-tested without constructing a full CLI
# invocation or using subprocess.


def _cmd_scaffold_agents_md(args: argparse.Namespace, root: Path) -> int:
    """Handler for the ``scaffold-agents-md`` subcommand."""
    overrides: dict[str, str] = {}
    for pair in args.set:
        if "=" not in pair:
            safe_print(f"FAIL: --set expects KEY=VALUE, got: {pair}", file=sys.stderr)
            return 1
        key, _, value = pair.partition("=")
        overrides[key] = value

    ci = args.ci
    if ci is None:
        env = analyze_project_env(root)
        ci = env.ci_provider
        if "ci" in Config.HARD_RULES_TEXT and ci not in Config.HARD_RULES_TEXT["ci"]:
            ci = "local-only"

    try:
        content = render_agents_md_skeleton(
            args.language,
            args.purpose,
            args.commit,
            args.maturity,
            args.testing,
            ci=ci,
            pm_override=args.pm,
            toolchain_overrides=overrides,
        )
    except ValueError as e:
        safe_print(f"FAIL: {e}", file=sys.stderr)
        return 1

    if args.out:
        out_path = args.out.resolve()
        # FIX S-3: reject --out paths outside the project root to prevent
        # write-anywhere exploitation via the scaffold subcommand.
        if not out_path.is_relative_to(root):
            safe_print(
                f"FAIL: --out path is outside the project root: {args.out}",
                file=sys.stderr,
            )
            return 1
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8", newline="\n")
            # FIX S-4: show path relative to root rather than absolute.
            safe_print(f"Wrote skeleton to {out_path.relative_to(root)}")
        except OSError as e:
            # FIX S-4: report only the filename, not the full resolved path.
            safe_print(
                f"FAIL: Could not write skeleton to {args.out.name}: {e}",
                file=sys.stderr,
            )
            return 1
    else:
        safe_print(content)
    return 0


def _cmd_analyze_all(args: argparse.Namespace, root: Path) -> int:
    """Handler for the ``analyze-all`` subcommand."""
    target = _resolve_target(args.target_dir, root)
    safe_print("### Environment")
    _print_env(analyze_project_env(target))
    safe_print("")
    safe_print("### Dependencies")
    _print_dependencies(get_dependencies(target))
    safe_print("")
    safe_print("### Structure")
    patterns = load_gitignore(target) | Config.DEFAULT_IGNORE_PATTERNS
    for line in get_tree_lines(target, patterns, args.max_depth):
        safe_print(line)
    return 0


def _add_target_dir_arg(parser: argparse.ArgumentParser, verb: str) -> None:
    """Add the optional positional ``target_dir`` argument shared by most subcommands."""
    parser.add_argument(
        "target_dir",
        type=Path,
        nargs="?",
        default=None,
        help=f"Directory to {verb} (default: current directory).",
    )


def _setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Consolidated plugin maintenance utilities."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint-agents-md", help="Validate AGENTS.md.")
    lint_parser.add_argument(
        "file_path", type=Path, nargs="?", default=Path("AGENTS.md")
    )

    analyze_env_parser = subparsers.add_parser(
        "analyze-env", help="Detect project environment."
    )
    _add_target_dir_arg(analyze_env_parser, "analyze")

    scan_parser = subparsers.add_parser(
        "scan-structure", help="Show directory structure."
    )
    _add_target_dir_arg(scan_parser, "scan")
    scan_parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum depth to recurse (default: 3).",
    )

    analyze_all_parser = subparsers.add_parser(
        "analyze-all",
        help="Run environment detection, dependency listing, and structure scan sequentially.",
    )
    _add_target_dir_arg(analyze_all_parser, "analyze")
    analyze_all_parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum depth for scan-structure (default: 3).",
    )

    wire_parser = subparsers.add_parser(
        "wire-agents",
        help="Write one-line redirect stubs in agent-specific files pointing to AGENTS.md.",
    )
    wire_parser.add_argument("source", type=Path, help="Source file (e.g. AGENTS.md).")
    wire_parser.add_argument(
        "targets",
        type=Path,
        nargs="+",
        help="Target files to create (e.g. CLAUDE.md GEMINI.md).",
    )

    scaffold_parser = subparsers.add_parser(
        "scaffold-agents-md",
        help="Print (or write) an AGENTS.md skeleton for a language, Hard Rules first.",
    )
    scaffold_parser.add_argument(
        "--language", required=True, choices=sorted(Config.LANGUAGE_DEFAULTS)
    )
    scaffold_parser.add_argument(
        "--purpose", default="<one sentence — what this repo does>"
    )
    scaffold_parser.add_argument(
        "--commit", required=True, choices=sorted(Config.HARD_RULES_TEXT["commit"])
    )
    scaffold_parser.add_argument(
        "--maturity", required=True, choices=sorted(Config.HARD_RULES_TEXT["maturity"])
    )
    scaffold_parser.add_argument(
        "--testing", required=True, choices=sorted(Config.HARD_RULES_TEXT["testing"])
    )
    scaffold_parser.add_argument(
        "--ci",
        choices=sorted(Config.HARD_RULES_TEXT["ci"])
        if "ci" in Config.HARD_RULES_TEXT
        else ["github-actions", "gitlab-ci", "local-only"],
        default=None,
        help="CI/CD Automation provider (default: auto-detected).",
    )
    scaffold_parser.add_argument(
        "--pm", default=None, help="Override the default package manager name."
    )
    scaffold_parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override a toolchain command discovered in Phase 1, e.g. --set test='npm test'.",
    )
    scaffold_parser.add_argument(
        "--out", type=Path, default=None, help="Write to this file instead of stdout."
    )
    return parser


def main() -> int:
    """Entry point for the CLI.

    Parses arguments, resolves the root directory and dispatches to the
    appropriate sub-command. Returns an appropriate exit status.
    """
    parser = _setup_parser()

    args = parser.parse_args()
    root = Path(".").resolve()

    match args.command:
        case "lint-agents-md":
            result = validate_agents_md_file(args.file_path)
            print_validation_issues(result)
            if result.success:
                safe_print("PASS: AGENTS.md is valid.")
            return 0 if result.success else 1
        case "analyze-env":
            target = _resolve_target(args.target_dir, root)
            _print_env(analyze_project_env(target))
            return 0
        case "scan-structure":
            target = _resolve_target(args.target_dir, root)
            patterns = load_gitignore(target) | Config.DEFAULT_IGNORE_PATTERNS
            lines = get_tree_lines(target, patterns, args.max_depth)
            for line in lines:
                safe_print(line)
            return 0
        case "analyze-all":
            return _cmd_analyze_all(args, root)
        case "wire-agents":
            return wire_agents_files(args.source, args.targets)
        case "scaffold-agents-md":
            return _cmd_scaffold_agents_md(args, root)
        case _:
            # FIX B-8: argparse with required=True exits before reaching this
            # branch; assert makes the invariant explicit instead of silently
            # returning 1 as unreachable dead code.
            assert False, f"unhandled command: {args.command}"  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
