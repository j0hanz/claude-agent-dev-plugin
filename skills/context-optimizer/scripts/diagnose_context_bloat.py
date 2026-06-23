#!/usr/bin/env python3
"""
Workspace Context Bloat Diagnostics script.
Checks file lengths, unignored heavy directories, lockfiles, and instruction stub consistency.
"""

import os
import sys
from pathlib import Path

BLOAT_LINE_LIMIT = 500
BLOAT_SIZE_LIMIT_KB = 50
HEAVY_DIRS = {".venv", "venv", "node_modules", "dist", "build", ".next", "target"}
LOCKFILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "go.sum",
}
TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".cpp",
    ".h",
    ".cs",
}


def parse_gitignore(root: Path) -> set[str]:
    # ponytail: heuristic line-based matcher, not full gitignore glob semantics
    ignore_patterns = set()
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        try:
            text = gitignore_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ignore_patterns
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                # Strip leading and trailing slashes to handle dir patterns correctly
                ignore_patterns.add(line.strip("/"))
    return ignore_patterns


def scan_files(
    root: Path, ignores: set[str]
) -> tuple[list[tuple[Path, str, int]], list[str]]:
    large_files: list[tuple[Path, str, int]] = []
    unignored_heavy_dirs: list[str] = []

    # Check for unignored heavy directories
    for d in HEAVY_DIRS:
        dir_path = root / d
        if dir_path.is_dir() and d not in ignores:
            unignored_heavy_dirs.append(d)

    # Recursive file walk with size/LOC checks
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude dot folders, heavy dirs, and gitignored dirs in-place
        dirnames[:] = [
            d
            for d in dirnames
            if d not in HEAVY_DIRS and d not in ignores and not d.startswith(".")
        ]

        for f in filenames:
            file_path = Path(dirpath) / f
            try:
                stat_result = file_path.stat()
                # Exclude lockfiles from LOC check, but flag them
                if f in LOCKFILES:
                    large_files.append((file_path, "Lockfile", stat_result.st_size))
                    continue

                size = stat_result.st_size
                size_kb = size / 1024

                if size_kb > BLOAT_SIZE_LIMIT_KB:
                    large_files.append((file_path, f"{size_kb:.1f} KB", size))
                    continue

                # LOC check for text files
                if file_path.suffix in TEXT_EXTENSIONS:
                    # Read line by line using a generator to avoid loading large files fully into memory
                    with file_path.open(encoding="utf-8", errors="ignore") as fp:
                        lines_count = sum(1 for _ in fp)
                    if lines_count > BLOAT_LINE_LIMIT:
                        large_files.append((file_path, f"{lines_count} lines", size))
            except OSError as exc:
                print(f"warning: skipped {file_path}: {exc}", file=sys.stderr)
                continue

    return large_files, unignored_heavy_dirs


def check_instruction_stubs(root: Path) -> list[str]:
    warnings = []
    stub_files = ["CLAUDE.md", "GEMINI.md", ".cursorrules"]
    for stub in stub_files:
        path = root / stub
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8", errors="ignore").strip()
            except OSError:
                continue
            # If the stub contains more than a redirect line AND does not contain AGENTS.md, raise warning
            if len(content.splitlines()) > 5 and "AGENTS.md" not in content:
                warnings.append(
                    f"`{stub}` does not appear to be a single-line stub referencing `AGENTS.md` (length={len(content.splitlines())} lines)."
                )
    return warnings


def main() -> None:
    root = Path(os.getcwd())
    ignores = parse_gitignore(root)
    large_files, unignored_dirs = scan_files(root, ignores)
    stub_warnings = check_instruction_stubs(root)

    print("## Workspace Context Bloat Diagnostics")
    print(f"Project Root: {root}\n")

    issues_found = False

    if unignored_dirs:
        print("### [WARNING] Unignored Heavy Directories:")
        for d in unignored_dirs:
            print(
                f"- `{d}/` exists but is not ignored in `.gitignore`. Indexing/searching may bloat context."
            )
        issues_found = True
        print()

    if large_files:
        print("### [WARNING] Bloat Candidates (Exceeding limits):")
        # Sort by size descending
        large_files.sort(key=lambda x: x[2], reverse=True)
        for path, reason, size in large_files:
            try:
                rel_path = path.relative_to(root)
            except ValueError:
                rel_path = path
            est_tokens = int(size / 3.7)
            print(
                f"- `{rel_path}` ({reason}) → Estimated: ~{est_tokens} tokens if read."
            )
        issues_found = True
        print()

    if stub_warnings:
        print("### [WARNING] Instruction Stub Warnings:")
        for warn in stub_warnings:
            print(f"- {warn}")
        issues_found = True
        print()

    if not issues_found:
        print("PASS: No bloating files or directories detected.")


if __name__ == "__main__":
    main()
