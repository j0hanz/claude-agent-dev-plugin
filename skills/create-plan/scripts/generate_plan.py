#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from typing import Protocol

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))
from spec_parser import parse_spec


class Spec(Protocol):
    sections: dict[str, str]
    reqs: list[str]
    acs: list[str]
    vals: list[str]


def generate_plan(spec: Spec, purpose: str, component: str) -> str:
    plan_lines = []

    # 1. Header
    plan_lines.append(
        f"# Implementation Plan: {purpose.replace('-', ' ').title()} - {component.replace('-', ' ').title()}"
    )
    plan_lines.append("")
    plan_lines.append("## Goal")
    goal = spec.sections.get("Goal", "[Pre-fill goal]")
    plan_lines.append(goal)
    plan_lines.append("")

    # 2. Phase 000: Setup & Discovery
    plan_lines.append("## PHASE-000: Setup & Discovery")
    plan_lines.append("### TASK-000: Verify environment and discover files")
    plan_lines.append("Depends on: none")
    plan_lines.append("Files: none")
    plan_lines.append("Symbols: none")
    plan_lines.append(
        'Action: Run `python skills/create-plan/scripts/discover.py --files "src/**/*"` to identify relevant files.'
    )
    plan_lines.append("Validate: discovery output is non-empty")
    plan_lines.append("Expected result: List of verified files is available.")
    plan_lines.append("")

    # 3. Implementation Phases
    # Group requirements into a single phase for the skeleton, or split if many
    plan_lines.append("## PHASE-001: Core Implementation")

    task_count = 1
    for req in sorted(spec.reqs):
        plan_lines.append(f"### TASK-{task_count:03}: Implement {req}")
        plan_lines.append("Depends on: TASK-000")
        plan_lines.append("Files: [UNVERIFIED: path/to/file.ts](path/to/file.ts)")
        plan_lines.append("Symbols: [UNVERIFIED: SymbolName](path/to/file.ts)")
        plan_lines.append(
            f"Action: Implement the logic required by {req} as specified in the spec."
        )
        plan_lines.append("Validate: [UNVERIFIED: command]")
        plan_lines.append(f"Expected result: Success signal for {req}.")
        plan_lines.append("")
        task_count += 1

    # 4. Phase END: Verification
    plan_lines.append("## PHASE-END: Verification & Cleanup")
    plan_lines.append(f"### TASK-{task_count:03}: Final acceptance testing")
    plan_lines.append(f"Depends on: TASK-{task_count - 1:03}")
    plan_lines.append("Files: none")
    plan_lines.append("Symbols: none")

    # Map ACs to validation
    ac_list = "\n".join(f"- {ac}" for ac in sorted(spec.acs))
    plan_lines.append(f"Action: Verify the following Acceptance Criteria:\n{ac_list}")

    val_cmd = "Manual check"
    if spec.vals:
        val_cmd = "; ".join(sorted(spec.vals))

    plan_lines.append(f"Validate: {val_cmd}")
    plan_lines.append("Expected result: All acceptance criteria are met.")
    plan_lines.append("")

    return "\n".join(plan_lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a plan skeleton from a specification."
    )
    parser.add_argument("spec", help="Path to the spec.md file")
    parser.add_argument(
        "--purpose", required=True, help="Plan purpose (e.g., feature, refactor)"
    )
    parser.add_argument(
        "--component", required=True, help="Target component (e.g., auth-module)"
    )
    args = parser.parse_args()

    try:
        spec = parse_spec(args.spec)
        plan_content = generate_plan(spec, args.purpose, args.component)
    except FileNotFoundError:
        print(f"Error: Spec file {args.spec} not found.")
        sys.exit(1)
    except Exception as e:
        raise RuntimeError(f"Plan generation failed for '{args.spec}': {e}") from e

    filename = f"{args.purpose}-{args.component}-1.md"
    print(f"--- GENERATED PLAN: {filename} ---")
    print(plan_content)


if __name__ == "__main__":
    main()
