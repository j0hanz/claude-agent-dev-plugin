#!/usr/bin/env python3
"""Local hook test harness.

Pipes sample event JSON to a hook command and reports exit code, parsed stdout
JSON (if any), and stderr — so a hook can be validated before it is registered.

Examples
--------
Single case, inline JSON:
    python test_hook.py --cmd "./protect-files.sh" \
        --input '{"tool_name":"Edit","tool_input":{"file_path":".env"}}'

Single case, JSON from a file:
    python test_hook.py --cmd "./check.sh" --input-file sample.json

Multiple cases from a JSON array file (each item: {name?, input, expect_exit?}):
    python test_hook.py --cmd "./check.sh" --cases cases.json

Exit code: 0 if every case ran (and matched expect_exit when given), else 1.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_case(cmd: str, payload: dict[str, Any], shell_cmd: bool) -> dict[str, Any]:
    """Run the hook once with `payload` on stdin; return a result dict."""
    stdin = json.dumps(payload)
    args = cmd if shell_cmd else shlex.split(cmd, posix=(sys.platform != "win32"))
    proc = subprocess.run(
        args,
        input=stdin,
        capture_output=True,
        text=True,
        shell=shell_cmd,
    )
    parsed = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass  # non-JSON stdout is valid for many events
    return {
        "exit": proc.returncode,
        "stdout": proc.stdout,
        "stdout_json": parsed,
        "stderr": proc.stderr,
    }


def report(name: str, result: dict[str, Any], expect_exit: int | None) -> bool:
    decision = {0: "no objection / proceed", 2: "BLOCK"}.get(
        result["exit"], "non-blocking error"
    )
    ok = expect_exit is None or result["exit"] == expect_exit
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}")
    print(f"  exit={result['exit']}  ({decision})")
    if expect_exit is not None and not ok:
        print(f"  expected exit={expect_exit}")
    if result["stdout_json"] is not None:
        print(f"  stdout JSON: {json.dumps(result['stdout_json'])}")
    elif result["stdout"].strip():
        print(f"  stdout: {result['stdout'].strip()[:500]}")
    if result["stderr"].strip():
        print(f"  stderr: {result['stderr'].strip()[:500]}")
    print()
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Test a Claude Code hook locally.")
    ap.add_argument("--cmd", required=True, help="Hook command to run.")
    ap.add_argument("--input", help="Inline JSON payload for a single case.")
    ap.add_argument("--input-file", help="Path to a JSON file with one payload.")
    ap.add_argument(
        "--cases", help="Path to a JSON array of {name?,input,expect_exit?}."
    )
    ap.add_argument(
        "--event", help="Label only; sets hook_event_name if absent in payload."
    )
    ap.add_argument("--expect-exit", type=int, help="Expected exit code (single case).")
    ap.add_argument("--shell", action="store_true", help="Run --cmd through the shell.")
    args = ap.parse_args()

    cases: list[dict[str, Any]] = []
    if args.cases:
        try:
            data = json.loads(Path(args.cases).read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"error: --cases file contains invalid JSON: {e}", file=sys.stderr)
            return 1
        if not isinstance(data, list):
            print("error: --cases file must contain a JSON array", file=sys.stderr)
            return 1
        cases = data
    elif args.input_file:
        try:
            payload = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"error: --input-file contains invalid JSON: {e}", file=sys.stderr)
            return 1
        cases = [{"input": payload}]
    elif args.input:
        try:
            payload = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(f"error: --input contains invalid JSON: {e}", file=sys.stderr)
            return 1
        cases = [{"input": payload, "expect_exit": args.expect_exit}]
    else:
        print("error: provide --input, --input-file, or --cases", file=sys.stderr)
        return 1

    all_ok = True
    for i, case in enumerate(cases, 1):
        payload = case.get("input", {})
        if args.event and "hook_event_name" not in payload:
            payload["hook_event_name"] = args.event
        name = case.get("name", f"case {i}")
        result = run_case(args.cmd, payload, args.shell)
        ok = report(name, result, case.get("expect_exit"))
        all_ok = all_ok and ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
