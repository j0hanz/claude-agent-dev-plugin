#!/usr/bin/env python3
"""validate_skill.py — Validate a SKILL.md against the parts of the Anthropic
skill spec and general best practice that the bundled checks below cover
(structural correctness, placeholder leftovers, dangling references, vague/
passive language, token budget, evals.json shape).

Usage:
    python validate_skill.py <name-or-path> [--strict]

<name-or-path> can be:
    - a bare skill name: validate_skill.py make-a-skill  (looks for
      .claude/skills/make-a-skill/SKILL.md or skills/make-a-skill/SKILL.md,
      resolved relative to cwd)
    - a path to SKILL.md or its containing directory

Exit code: 0 if no errors (warnings never fail the run unless --strict),
1 if any error found (or any warning, under --strict).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PLACEHOLDER_MARKER = "{{FILL"

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)

# Markdown link targets and bare-backtick paths under these dirs are checked
# for existence relative to the skill directory.
LINKED_DIR_PATH_RE = re.compile(r"(?:\]\(|`)((?:references|scripts|evals)/[^\s`)]+)")

VAGUE_ADJECTIVES: tuple[str, ...] = (
    "lightweight",
    "clean",
    "robust",
    "fast",
    "performant",
    "easy",
    "simple",
)
_PASSIVE_VOICE_RE = re.compile(
    r"\bbe\s+(?!(?:red|bed|fed|led|shed|indeed|tired|bleed|speed|feed)\b)\w+ed\b",
    re.IGNORECASE,
)
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _strip_code(text: str) -> str:
    """Remove fenced/inline code spans so prose *about* the {{FILL marker
    (e.g. this skill's own SKILL.md explaining the convention in backticks)
    isn't mistaken for a literal unfilled placeholder."""
    return _INLINE_CODE_RE.sub("", _FENCED_CODE_RE.sub("", text))


DESC_MIN_LEN = 40
DESC_MAX_LEN = 1024
# Anthropic spec guideline: keep SKILL.md body under ~5000 tokens; estimate
# tokens as chars / 4 (no tokenizer dependency). This is a different signal
# than bin/validate-plugin.mjs's line-count>300 check, so it stays additive.
TOKEN_BUDGET = 5000
CHARS_PER_TOKEN_ESTIMATE = 4


# ---------------------------------------------------------------------------
# Frontmatter parsing (no external YAML dependency — SKILL.md frontmatter is
# always a flat key: value block, never nested)
# ---------------------------------------------------------------------------


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str] | None:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", content, re.DOTALL)
    if not match:
        return None
    raw, body = match.group(1), content[match.end() :]
    fields: dict[str, str] = {}
    current_key = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if current_key and (line.startswith(" ") or line.startswith("\t")):
            fields[current_key] += "\n" + line.strip()
            continue
        kv_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not kv_match:
            continue
        key, value = kv_match.group(1), kv_match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key] = value
        current_key = key
    return fields, body


# ---------------------------------------------------------------------------
# Individual checks — each returns (errors, warnings)
# ---------------------------------------------------------------------------


def validate_frontmatter(
    skill_dir: Path, fields: dict[str, str] | None
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if fields is None:
        errors.append("[FRONTMATTER] Missing YAML frontmatter block (--- ... ---)")
        return errors, warnings

    name = fields.get("name", "")
    description = fields.get("description", "")

    if not name:
        errors.append("[FRONTMATTER] Missing 'name' field")
    else:
        if name != skill_dir.name:
            errors.append(
                f"[FRONTMATTER] name {name!r} does not match directory name {skill_dir.name!r}"
            )
        if not KEBAB_RE.match(name):
            errors.append(
                f"[FRONTMATTER] name {name!r} is not kebab-case (lowercase, hyphen-separated)"
            )

    if not description:
        errors.append("[FRONTMATTER] Missing 'description' field")
    elif PLACEHOLDER_MARKER in description:
        errors.append(
            "[FRONTMATTER] description still contains an unfilled '{{FILL' placeholder"
        )
    else:
        if len(description) < DESC_MIN_LEN:
            warnings.append(
                f"[FRONTMATTER] description is only {len(description)} chars — "
                "likely too terse for Claude to judge when to invoke this skill"
            )
        elif len(description) > DESC_MAX_LEN:
            warnings.append(
                f"[FRONTMATTER] description is {len(description)} chars, over the "
                f"practical ~{DESC_MAX_LEN}-char ceiling"
            )
        if "Trigger on:" not in description:
            warnings.append(
                "[FRONTMATTER] description has no \"Trigger on: '...'\" clause — "
                "recommended so Claude can match literal user phrases to this skill"
            )

    disable_model_invocation = fields.get("disable-model-invocation")
    if disable_model_invocation is not None and disable_model_invocation not in (
        "true",
        "false",
    ):
        warnings.append(
            f"[FRONTMATTER] disable-model-invocation {disable_model_invocation!r} should "
            "be the lowercase boolean literal 'true' or 'false'"
        )

    return errors, warnings


def validate_body(body: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    stripped_body = _strip_code(body)
    unfilled = stripped_body.count(PLACEHOLDER_MARKER)
    if unfilled:
        errors.append(
            f"[BODY] {unfilled} unfilled '{{{{FILL: ...}}}}' placeholder(s) remain in the body"
        )

    for adj in VAGUE_ADJECTIVES:
        if re.search(rf"\b{re.escape(adj)}\b", stripped_body, re.IGNORECASE):
            warnings.append(
                f"[BODY] Vague adjective '{adj}' found - prefer a concrete, checkable claim"
            )

    for line in stripped_body.splitlines():
        if _PASSIVE_VOICE_RE.search(line):
            warnings.append(f"[BODY] Possible passive voice: {line.strip()[:100]}")

    line_count = len(body.splitlines())
    token_estimate = len(body) // CHARS_PER_TOKEN_ESTIMATE
    if token_estimate > TOKEN_BUDGET:
        warnings.append(
            f"[BODY] Estimated ~{token_estimate} tokens exceeds the spec's "
            f"{TOKEN_BUDGET}-token guideline ({line_count} lines) — move detail to references/"
        )

    return errors, warnings


def validate_references(skill_dir: Path, body: str) -> tuple[list[str], list[str]]:
    """Errors: a markdown link or backtick path under references/scripts/evals
    that points at a file that doesn't exist (catches typos/renames).
    Warnings: a top-level file directly in scripts/ or references/ whose
    filename never appears anywhere in the body. Scoped to top-level files
    only (not nested helper/test/fixture files) and by filename substring
    (not full relative path) because most skills invoke scripts via a
    $CLAUDE_PLUGIN_ROOT-prefixed shell command inside a code fence, not a
    bare backtick-wrapped relative path.
    """
    errors: list[str] = []
    warnings: list[str] = []

    missing: set[str] = set()
    # Strip fenced (triple-backtick) blocks only — not inline single-backtick
    # spans, since a bare backtick-wrapped relative path is exactly what this
    # check is meant to catch (see test_dangling_reference_link_is_error).
    unfenced_body = _FENCED_CODE_RE.sub("", body)
    skill_dir_resolved = skill_dir.resolve()
    for match in LINKED_DIR_PATH_RE.finditer(unfenced_body):
        rel_path = match.group(1).rstrip(".,;:)")
        file_path_part = rel_path.split("#")[0]
        target = (skill_dir / file_path_part).resolve()
        # A "../" link that escapes skill_dir is treated as dangling too, not followed.
        if not target.is_relative_to(skill_dir_resolved) or not target.exists():
            missing.add(rel_path)
    for rel_path in sorted(missing):
        errors.append(
            f"[REFERENCES] SKILL.md links to '{rel_path}' which does not exist"
        )

    for sub in ("references", "scripts"):
        sub_dir = skill_dir / sub
        if not sub_dir.is_dir():
            continue
        for path in sub_dir.iterdir():
            if (
                not path.is_file()
                or path.name.startswith("test_")
                or path.name.startswith(".")
                or path.name == "__init__.py"
            ):
                continue
            if path.name not in body:
                warnings.append(
                    f"[REFERENCES] '{sub}/{path.name}' exists but is never mentioned in SKILL.md's body"
                )

    return errors, warnings


def _has_fill_placeholder(val: Any) -> bool:
    if isinstance(val, str):
        return "FILL:" in val
    if isinstance(val, list):
        return any(_has_fill_placeholder(x) for x in val)
    if isinstance(val, dict):
        return any(
            _has_fill_placeholder(k) or _has_fill_placeholder(v) for k, v in val.items()
        )
    return False


def validate_evals(skill_dir: Path) -> tuple[list[str], list[str]]:
    """Check evals.json is well-formed. Two schemas are both accepted: a bare
    top-level array of cases, or {"skill_name", "evals": [...]}. Case objects
    also commonly vary in field naming ("assertions" vs "expectations"), so
    only "prompt" is treated as required.
    """
    errors: list[str] = []
    warnings: list[str] = []

    evals_path = skill_dir / "evals" / "evals.json"
    if not evals_path.exists():
        return errors, warnings

    try:
        data = json.loads(evals_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        errors.append(f"[EVALS] evals.json is not valid JSON: {e}")
        return errors, warnings

    if isinstance(data, list):
        cases = data
    elif isinstance(data, dict):
        if "skill_name" in data and data.get("skill_name") != skill_dir.name:
            warnings.append(
                f"[EVALS] evals.json 'skill_name' ({data.get('skill_name')!r}) does not "
                f"match the skill directory ({skill_dir.name!r})"
            )
        if "evals" not in data:
            errors.append("[EVALS] evals.json object form must have an 'evals' key")
            return errors, warnings
        cases = data["evals"]
    else:
        errors.append("[EVALS] evals.json must be a JSON array or object")
        return errors, warnings

    if not isinstance(cases, list) or not cases:
        errors.append("[EVALS] evals.json must contain a non-empty list of eval cases")
        return errors, warnings

    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"[EVALS] evals[{i}] must be an object")
            continue
        if "prompt" not in case:
            errors.append(f"[EVALS] evals[{i}] missing required field 'prompt'")
        if not ({"assertions", "expectations"} & case.keys()):
            warnings.append(
                f"[EVALS] evals[{i}] has neither 'assertions' nor 'expectations' — "
                "no checkable success criteria"
            )
        if _has_fill_placeholder(case):
            errors.append(
                f"[EVALS] evals[{i}] still contains an unfilled 'FILL:' placeholder"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _resolve_skill_md(name_or_path: str) -> Path:
    p = Path(name_or_path)
    if p.name == "SKILL.md":
        return p.resolve()
    if p.is_dir():
        return (p / "SKILL.md").resolve()
    if len(p.parts) == 1:
        for skills_dir in (Path(".claude/skills"), Path("skills")):
            candidate = skills_dir / p.name / "SKILL.md"
            if candidate.exists():
                return candidate.resolve()
        # Not found under either root — report against the conventional one
        # so the "not found" message points somewhere meaningful.
        return (Path(".claude/skills") / p.name / "SKILL.md").resolve()
    return (p / "SKILL.md").resolve()


def validate_skill(skill_md: Path) -> tuple[list[str], list[str]]:
    if not skill_md.exists():
        return [f"SKILL.md not found: {skill_md}"], []

    skill_dir = skill_md.parent
    content = skill_md.read_text(encoding="utf-8-sig")  # tolerate a BOM
    parsed = _parse_frontmatter(content)
    fields, body = (parsed[0], parsed[1]) if parsed else (None, content)

    all_errors: list[str] = []
    all_warnings: list[str] = []
    for errs, warns in (
        validate_frontmatter(skill_dir, fields),
        validate_body(body),
        validate_references(skill_dir, body),
        validate_evals(skill_dir),
    ):
        all_errors.extend(errs)
        all_warnings.extend(warns)

    return all_errors, all_warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a skills/<name>/SKILL.md against local conventions."
    )
    parser.add_argument("name", help="Skill name or path to SKILL.md / its directory")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as failures too"
    )
    args = parser.parse_args()

    skill_md = _resolve_skill_md(args.name)
    print(f"--- {skill_md} ---")
    errors, warnings = validate_skill(skill_md)

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  [X] {e}")
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  [!] {w}")

    failed = bool(errors) or (args.strict and bool(warnings))
    print(
        f"\n{'INVALID' if failed else 'VALID'} "
        f"({len(errors)} error(s), {len(warnings)} warning(s))"
    )
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"validate_skill.py: {e}", file=sys.stderr)
        sys.exit(1)
