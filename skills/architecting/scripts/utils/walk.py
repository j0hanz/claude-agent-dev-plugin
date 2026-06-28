import os
from typing import List, Optional

DEFAULT_EXCLUDE = [
    "node_modules",
    ".test.",
    ".spec.",
    ".git",
    ".svn",
    ".hg",
    ".pytest_cache",
    ".tox",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "dist",
    "build",
    "coverage",
    ".coverage",
    ".next",
    ".nuxt",
    ".cache",
    ".parcel",
    ".npm",
    ".yarn",
    "target",
    ".gradle",
    ".m2",
    ".pytest",
    ".mypy_cache",
    ".ruff_cache",
    ".vscode",
    ".idea",
    ".DS_Store",
]


_EXTS = (".ts", ".tsx", ".js", ".mjs", ".py", ".go")


def walk_dir(root_dir: str, exclude: Optional[List[str]] = None) -> List[str]:
    """
    Recursively walk a directory, returning paths of TypeScript/JavaScript, Python, and Go files.
    """
    exclude = exclude or []
    files = []
    # followlinks=False: never re-descend into symlinked dirs, so no cycle tracking needed
    for dirpath, dirnames, filenames in os.walk(
        root_dir, followlinks=False, onerror=lambda e: None
    ):
        dirnames[:] = [d for d in dirnames if not any(pat in d for pat in exclude)]
        for name in filenames:
            if not any(pat in name for pat in exclude) and name.endswith(_EXTS):
                files.append(os.path.abspath(os.path.join(dirpath, name)))
    return files
