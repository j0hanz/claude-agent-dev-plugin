#!/usr/bin/env python3
"""Context pruning and formatting tool.

Compresses log files, filters stack traces, converts JSON to markdown-kv,
and maintains rolling context summaries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Hoisted error patterns to prevent recompilation on every call
_ERROR_PATTERNS = [
    re.compile(r"fail", re.I),
    re.compile(r"error", re.I),
    re.compile(r"exception", re.I),
    re.compile(r"traceback", re.I),
    re.compile(r"critical", re.I),
    re.compile(r"\b(at)\s+\S+:\d+", re.I),
    re.compile(r"^E\s+.*", re.M),
]


def to_markdown_kv(data: Any, prefix: str = "", depth: int = 0) -> list[str]:
    """Recursively converts dictionaries and lists into a flat, compact markdown-kv string."""
    if depth > 50:
        raise ValueError("Exceeded maximum nesting depth of 50 in JSON object")
    if depth == 0:
        if isinstance(data, dict) and not data:
            return ["(empty object)"]
        if isinstance(data, list) and not data:
            return ["(empty array)"]
        if not isinstance(data, (dict, list)):
            raise ValueError(
                f"top-level JSON must be an object or array, got {type(data).__name__}"
            )

    lines = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{prefix}_{k}" if prefix else k
            lines.extend(to_markdown_kv(v, new_key, depth + 1))
    elif isinstance(data, list):
        if not data:
            lines.append(f"{prefix}: (empty)")
        elif all(isinstance(x, (str, int, float, bool)) for x in data):
            val_str = ", ".join(str(x) for x in data)
            lines.append(f"{prefix}: {val_str}")
        else:
            for idx, item in enumerate(data):
                new_key = f"{prefix}_{idx}"
                lines.extend(to_markdown_kv(item, new_key, depth + 1))
    else:
        lines.append(f"{prefix}: {data}")
    return lines


def filter_logs(logs_text: str) -> str:
    """Filters logs to retain only failure signals, tracebacks, and test failures."""
    lines = [line.rstrip() for line in logs_text.splitlines()]
    if not lines:
        return "empty log"

    error_indices = []
    for idx, line in enumerate(lines):
        if any(pat.search(line) for pat in _ERROR_PATTERNS):
            error_indices.append(idx)

    if not error_indices:
        head, tail = 5, 5
        if len(lines) <= head + tail:
            return "\n".join(lines)
        return (
            "\n".join(lines[:head])
            + f"\n... [omitted {len(lines) - head - tail} lines of passing logs] ...\n"
            + "\n".join(lines[-tail:])
        )

    keep_indices = set()
    for err_idx in error_indices:
        start = max(0, err_idx - 2)
        end = min(len(lines), err_idx + 8)
        for i in range(start, end):
            keep_indices.add(i)

    sorted_indices = sorted(keep_indices)
    output_parts = []
    last_idx = -1

    for idx in sorted_indices:
        if last_idx != -1 and idx > last_idx + 1:
            output_parts.append(f"... [omitted {idx - last_idx - 1} lines] ...")
        output_parts.append(lines[idx])
        last_idx = idx

    result = "\n".join(output_parts)
    result_lines = result.splitlines()
    head, tail = 40, 10
    if len(result_lines) > head + tail:
        return (
            "\n".join(result_lines[:head])
            + f"\n... [omitted {len(result_lines) - head - tail} lines of error details] ...\n"
            + "\n".join(result_lines[-tail:])
        )
    return result


def update_rolling_summary(
    summary_path: Path,
    timestamp: str,
    done: str,
    blocking: str,
    next_step: str,
    decisions: str,
    current_skill: str = "None",
) -> str:
    """Updates the rolling summary file, archiving previous sessions."""
    existing_entries: list[str] = []
    if summary_path.exists():
        try:
            content = summary_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = ""
        # Split on markdown section headers for Session
        parts = re.split(r"^## Session:\s*", content, flags=re.M)
        for part in parts[1:]:
            existing_entries.append(part.strip())

    new_block = (
        f"timestamp: {timestamp}\n"
        f"current_skill: {current_skill}\n"
        f"done: {done}\n"
        f"blocking: {blocking}\n"
        f"next: {next_step}\n"
        f"key_decisions: {decisions}"
    )

    merged_history = []
    for idx, entry in enumerate(existing_entries):
        lines = entry.splitlines()
        if not lines:
            continue
        header_line = lines[0].strip()
        ts_match = re.match(r"^([^\s(]+)", header_line)
        ts = ts_match.group(1) if ts_match else header_line

        # Archive after the second session, keep full detail for recent sessions
        body = "\n".join(lines[1:]).strip()

        if idx < 2:
            merged_history.append(f"## Session: {header_line}\n{body}")
        else:
            # Check if it was already marked as archived to avoid prepending/losing labels
            display_header = (
                header_line if "Archived" in header_line else f"{ts} (Archived)"
            )
            done_line = "No actions recorded"
            for line in lines[1:]:
                if line.startswith("done:"):
                    done_line = line.replace("done:", "").strip()
                    break
            merged_history.append(f"## Session: {display_header}\n- {done_line}")

    output = [
        "# Rolling Task Summary\n",
        f"## Session: {timestamp} (Current)",
        new_block,
        "",
    ]
    if merged_history:
        output.extend(merged_history)

    final_content = "\n".join(output)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(final_content, encoding="utf-8")
    return final_content


def append_task_ledger(summary_path: Path, task_line: str) -> str:
    """Appends a line to the Task Ledger section, creating it if needed (FIFO order)."""
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content
    content = ""
    if summary_path.exists():
        try:
            content = summary_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass

    # Check if Task Ledger section exists
    if "## Task Ledger" in content:
        lines = content.split("\n")
        # Find the Task Ledger heading
        ledger_idx = -1
        for i, line in enumerate(lines):
            if line.strip() == "## Task Ledger":
                ledger_idx = i
                break

        if ledger_idx >= 0:
            # Find the last task entry (Task N: complete ...) in the ledger section
            insert_pos = ledger_idx + 1
            last_task_idx = ledger_idx

            for i in range(ledger_idx + 1, len(lines)):
                # Stop at the next section heading
                if lines[i].startswith("#"):
                    break
                # Track the last task entry line
                if lines[i].strip().startswith("Task ") and ": complete" in lines[i]:
                    last_task_idx = i

            # Insert after the last task entry, or after the heading if no entries exist
            insert_pos = last_task_idx + 1

            output = lines[:insert_pos] + [task_line] + lines[insert_pos:]
            final_content = "\n".join(output)
        else:
            final_content = content
    else:
        # Create the section at the end
        if content and not content.endswith("\n"):
            content += "\n"
        final_content = content + "\n## Task Ledger\n" + task_line + "\n"

    summary_path.write_text(final_content, encoding="utf-8")
    return final_content


def main() -> None:
    parser = argparse.ArgumentParser(description="Prune and optimize context input.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--logs", action="store_true", help="Filter raw logs from stdin")
    group.add_argument(
        "--to-kv", action="store_true", help="Convert JSON input to flat KV"
    )
    group.add_argument(
        "--summary", action="store_true", help="Update the rolling summary file"
    )
    group.add_argument(
        "--task-complete",
        default=None,
        help='Append a line to the Task Ledger (e.g., "Task N: complete (commits <base7>..<head7>, review clean)")',
    )

    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Summary path (default: <cwd>/.claude/rolling_summary.md)",
    )
    parser.add_argument("--timestamp", default="", help="Timestamp of current session")
    parser.add_argument(
        "--current-skill",
        default="None",
        help="Active skill/gate, so resume doesn't re-derive routing from scratch",
    )
    parser.add_argument("--done", default="None", help="Completed tasks")
    parser.add_argument("--blocking", default="None", help="Blocking issues")
    parser.add_argument("--next-step", default="None", help="Immediate next action")
    parser.add_argument("--decisions", default="None", help="Key decisions made")

    args = parser.parse_args()
    if args.path is None:
        args.path = Path.cwd() / ".claude" / "rolling_summary.md"

    if args.logs:
        text = sys.stdin.read()
        print(filter_logs(text))
    elif args.to_kv:
        try:
            raw = json.loads(sys.stdin.read())
            kv_lines = to_markdown_kv(raw)
            print("\n".join(kv_lines))
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"error: invalid JSON input - {exc}\n")
            sys.exit(1)
        except ValueError as exc:
            sys.stderr.write(f"error: {exc}\n")
            sys.exit(1)
    elif args.summary:
        if not args.timestamp or not args.timestamp.strip():
            sys.stderr.write(
                "error: --timestamp is required for updating the summary\n"
            )
            sys.exit(1)
        result = update_rolling_summary(
            args.path,
            args.timestamp,
            args.done,
            args.blocking,
            args.next_step,
            args.decisions,
            args.current_skill,
        )
        print(f"Summary written to {args.path}. Content:")
        print(result)
    elif args.task_complete:
        result = append_task_ledger(args.path, args.task_complete)
        print(f"Task ledger entry written to {args.path}. Content:")
        print(result)


if __name__ == "__main__":
    main()
