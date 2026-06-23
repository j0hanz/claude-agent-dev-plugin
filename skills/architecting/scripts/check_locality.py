"""Module for checking code locality and detecting circular dependencies.

This script analyzes Python, JavaScript/TypeScript, and Go files to construct
an import graph, find circular dependencies, and compute file import fan-out.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from utils.extractor import extract_imports, detect_lang
from utils.graph import find_cycles
from utils.walk import walk_dir, DEFAULT_EXCLUDE


def import_candidates(from_file: str, imp: str, lang: str) -> list[str]:
    """Generate possible file path candidates for a given relative import.

    Args:
        from_file: The path to the file containing the import.
        imp: The import specifier string (e.g., './module' or '..module').
        lang: The file language/extension ('py', 'js', 'go', etc.).

    Returns:
        A list of resolved candidate file paths to check for existence.
    """
    from_path = Path(from_file)
    from_dir = from_path.parent

    if lang == "py":
        # Leading dots are package levels: one dot = current package (same dir),
        # each extra dot = one parent up.
        dots = 0
        while dots < len(imp) and imp[dots] == ".":
            dots += 1

        if dots == 0:
            # Absolute import or not relative in the expected way
            # But locality check only cares about relative imports (starting with '.')
            return []

        rest = imp[dots:].split(".")
        rest = [r for r in rest if r]

        base = from_dir
        for _ in range(1, dots):
            base = base.parent

        resolved = base.joinpath(*rest)
        # ponytail: bare "from . import x" (rest=[]) only resolves via __init__.py;
        # PEP 420 namespace packages without __init__.py won't match. Fix if that
        # pattern shows up: capture the imported names and try them as submodules.
        return [f"{resolved}.py", str(resolved / "__init__.py")]

    # js / go
    resolved = (from_dir / imp).resolve()
    candidates = []

    basename = Path(imp).name
    if "." in basename:
        # Import already carries an extension
        candidates.append(str(resolved))
        # TS allows a '.js' specifier to resolve to the '.ts' source.
        no_ext = resolved.with_suffix("")
        candidates.extend([f"{no_ext}.ts", f"{no_ext}.tsx"])

    candidates.extend(
        [
            f"{resolved}.ts",
            f"{resolved}.tsx",
            f"{resolved}.js",
            f"{resolved}.jsx",
            f"{resolved}.mjs",
            f"{resolved}.cjs",
            f"{resolved}.go",
            str(resolved / "index.ts"),
            str(resolved / "index.tsx"),
            str(resolved / "index.js"),
            str(resolved / "index.jsx"),
            str(resolved / "index.mjs"),
        ]
    )
    return candidates


def run_locality_check(
    target_dir: str | Path, exclude: list[str] | None = None
) -> tuple[list[list[str]], list[dict[str, Any]]]:
    """Analyze a directory to find circular dependencies and top fan-out files.

    Args:
        target_dir: The directory to analyze.
        exclude: List of directory names or patterns to exclude.

    Returns:
        A tuple containing:
            - A list of cycles (each cycle is a list of file paths).
            - A list of dictionaries representing fan-out (highest imports).
    """
    if exclude is None:
        exclude = DEFAULT_EXCLUDE

    files = walk_dir(str(target_dir), exclude)
    graph = {}

    for file_path in files:
        try:
            content = Path(file_path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        lang = detect_lang(file_path)
        imports = extract_imports(content, lang)
        graph[file_path] = []

        for imp in imports:
            # Only care about relative imports for locality
            if not imp.startswith("."):
                continue

            for candidate in import_candidates(file_path, imp, lang):
                if Path(candidate).exists():
                    graph[file_path].append(candidate)
                    break

    cycles = find_cycles(graph)

    # Calculate Fan-out
    fan_out = []
    for file, deps in graph.items():
        fan_out.append({"file": file, "count": len(deps)})

    fan_out.sort(key=lambda x: x["count"], reverse=True)

    return cycles, fan_out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check locality and circular dependencies."
    )
    parser.add_argument("dir", nargs="?", default="src", help="Directory to analyze")

    args = parser.parse_args()

    print(f"Checking locality in {args.dir}...")
    abs_dir = Path(args.dir).resolve()

    try:
        cycles, fan_out = run_locality_check(abs_dir)

        print("\n--- Circular Dependencies ---")
        if not cycles:
            print("None found.")
        else:
            for i, cycle in enumerate(cycles):
                print(f"\nCycle {i + 1}:")
                for node in cycle:
                    print(f"  - {os.path.relpath(node, Path.cwd())}")

        print("\n--- Top 5 Fan-out (Highest Imports) ---")
        for item in fan_out[:5]:
            print(
                f"  - {os.path.relpath(item['file'], Path.cwd())} ({item['count']} imports)"
            )

    except FileNotFoundError:
        print(f"Directory not found: {args.dir}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
