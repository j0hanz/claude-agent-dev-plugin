#!/usr/bin/env python3
"""Behavioral test harness for agents using Claude Code's hook protocol.

Usage:
  python scripts/simulate.py <agent.md> <cases.yaml> [options]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

from simulator import (
    evaluate_assertions,
    parse_tool_calls_jsonl,
    aggregate_runs,
    RunResult,
)


def _safety_check(args) -> tuple[bool, str]:
    if os.environ.get("CLAUDE_CODE_REMOTE") == "true":
        return (False, "refusing to simulate in remote web environment")
    if args.worktree or args.sandbox:
        return True, ""
    cwd = Path.cwd().resolve()
    tmp_prefix = Path(tempfile.gettempdir()).resolve()
    try:
        cwd.relative_to(tmp_prefix)
        return True, ""
    except ValueError:
        return (
            False,
            "safety precondition not met: pass --worktree or --sandbox, or run inside tmpdir",
        )


async def _write_observer(simulate_dir: Path) -> Path:
    await asyncio.to_thread(simulate_dir.mkdir, parents=True, exist_ok=True)
    obs = simulate_dir / "observer.py"
    src = Path(__file__).parent / "lib" / "observer.py"
    await asyncio.to_thread(shutil.copy2, src, obs)
    return obs


async def _write_hooks_config(simulate_dir: Path, observer: Path) -> Path:
    cfg = {
        "hooks": {
            ev: [
                {
                    "matcher": ".*" if ev in {"PreToolUse", "PostToolUse"} else "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{sys.executable} {observer}",
                            "timeout": 5,
                        }
                    ],
                }
            ]
            for ev in ("PreToolUse", "PostToolUse", "Stop")
        }
    }
    out = simulate_dir / "hooks-config.json"
    await asyncio.to_thread(out.write_text, json.dumps(cfg, indent=2), encoding="utf-8")
    return out


def _load_cases(path: Path) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


async def run_case(
    case: dict, agent_file: Path, hooks_config: Path, runs: int, simulate_dir: Path
) -> list[RunResult]:
    prompt = case.get("prompt", "")
    expect = case.get("expect", {})
    results = []

    for i in range(runs):
        run_id = f"{case.get('id', 'case')}-run-{i}"
        run_dir = simulate_dir / "runs" / run_id
        await asyncio.to_thread(run_dir.mkdir, parents=True, exist_ok=True)

        env = os.environ.copy()
        env["SIMULATE_RUN_ID"] = run_id
        env["SIMULATE_OUT_DIR"] = str(simulate_dir / "runs")
        env["CLAUDE_CONFIG_DIR"] = str(run_dir / ".claude-config")
        env["CLAUDE_HOOKS_CONFIG"] = str(hooks_config)

        effective_prompt = prompt
        if agent_file:
            try:
                from lib.agent_parser import parse_agent  # noqa: PLC0415

                agent_spec = parse_agent(agent_file)
                system_preamble = f"[SYSTEM PROMPT]\n{agent_spec.system_prompt}\n[END SYSTEM PROMPT]\n\n"
                effective_prompt = system_preamble + prompt
            except Exception:
                pass

        cmd = ["claude", "-p", effective_prompt, "--output-format", "json"]

        start_time = time.time()
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            duration_s = time.time() - start_time

            try:
                out_data = json.loads(stdout.decode())
                final_response = out_data.get("result", "")
                tokens_in = out_data.get("usage", {}).get("input_tokens", 0)
                tokens_out = out_data.get("usage", {}).get("output_tokens", 0)
            except Exception:
                final_response = stdout.decode(errors="replace")
                tokens_in = tokens_out = 0

            log_file = run_dir / "tool-calls.jsonl"
            calls = []
            if await asyncio.to_thread(log_file.exists):
                log_content = await asyncio.to_thread(
                    log_file.read_text, encoding="utf-8"
                )
                calls = parse_tool_calls_jsonl(log_content)

            eval_res = evaluate_assertions(calls, final_response, expect, duration_s)

            results.append(
                RunResult(
                    passed=eval_res.passed,
                    duration_ms=int(duration_s * 1000),
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                )
            )

        except asyncio.TimeoutError:
            process.terminate()
            await process.wait()
            results.append(RunResult(False, 300000, 0, 0))
        except Exception as e:
            print(f"Run {run_id} failed: {e}")
            results.append(RunResult(False, 0, 0, 0))

    return results


async def main_async():
    p = argparse.ArgumentParser()
    p.add_argument("agent_file")
    p.add_argument("cases_file")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--worktree", action="store_true")
    p.add_argument("--sandbox", action="store_true")
    p.add_argument("--simulate-dir", default=".simulate")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and write observer files without running claude",
    )
    p.add_argument(
        "--report",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = p.parse_args()

    ok, reason = _safety_check(args)
    if not ok:
        print(f"error: {reason}")
        sys.exit(2)

    agent_path = Path(args.agent_file)
    cases_path = Path(args.cases_file)
    cases_data = _load_cases(cases_path)

    simulate_dir = Path(args.simulate_dir)
    observer = await _write_observer(simulate_dir)
    hooks_cfg = await _write_hooks_config(simulate_dir, observer)

    if args.dry_run:
        if args.report == "json":
            payload = {
                "dry_run": True,
                "suite": cases_data.get("suite", "default"),
                "safety_checks_passed": True,
                "agent": str(agent_path),
                "cases": len(cases_data.get("cases", [])),
                "simulate_dir": str(simulate_dir),
                "observer": str(observer),
                "hooks_config": str(hooks_cfg),
            }
            print(json.dumps(payload))
        else:
            suite_name = cases_data.get("suite", "default")
            cases = cases_data.get("cases", [])
            print(f"[dry-run] Suite: {suite_name}")
            print(f"[dry-run] Agent: {agent_path}")
            print(f"[dry-run] Cases ({len(cases)}):")
            for c in cases:
                print(
                    f"  - {c.get('name', c.get('id', 'unnamed'))}: {c.get('prompt', '')[:60]}"
                )
            print(f"[dry-run] Observer written to: {observer}")
            print(f"[dry-run] Hooks config written to: {hooks_cfg}")
        sys.exit(0)

    suite_results: dict[str, Any] = {}

    print(f"Running simulation suite: {cases_data.get('suite', 'default')}")

    for case in cases_data.get("cases", []):
        case_id = case.get("id", "unknown")
        print(f"  Case: {case_id}...", end="", flush=True)
        results = await run_case(case, agent_path, hooks_cfg, args.runs, simulate_dir)
        summary = aggregate_runs(results)
        suite_results[case_id] = summary
        print(f" {summary['pass_rate'] * 100:.0f}% pass")

    # Final report
    if args.report == "json":
        print(json.dumps(suite_results))
    else:
        print("\n## Simulation Report\n")
        for case_id, summary in suite_results.items():
            status = (
                "PASS"
                if summary["pass_rate"] == 1.0
                else "PARTIAL"
                if summary["pass_rate"] > 0
                else "FAIL"
            )
            print(
                f"- {status} **{case_id}**: {summary['pass_rate'] * 100:.0f}% pass "
                f"(n={summary['n']}), {summary['median_latency_ms']}ms median"
            )

    if all(s["pass_rate"] == 1.0 for s in suite_results.values()):
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main_async())
