import argparse
import json
import random
import sys
import tempfile
import time
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_report import generate_html
from scripts.improve_description import improve_description
from scripts.json_utils import load_json, save_json
from scripts.run_eval import find_project_root, run_eval
from scripts.utils import parse_skill_md


def split_eval_set(eval_set: list[dict], holdout: float, seed: int = 42) -> tuple[list[dict], list[dict]]:
    random.seed(seed)
    trigger = [e for e in eval_set if e["should_trigger"]]
    no_trigger = [e for e in eval_set if not e["should_trigger"]]
    random.shuffle(trigger)
    random.shuffle(no_trigger)
    n_trigger_test = max(1, int(len(trigger) * holdout))
    n_no_trigger_test = max(1, int(len(no_trigger) * holdout))
    test_set = trigger[:n_trigger_test] + no_trigger[:n_no_trigger_test]
    train_set = trigger[n_trigger_test:] + no_trigger[n_no_trigger_test:]
    return train_set, test_set


def _run_iteration(
    iteration: int,
    current_description: str,
    train_set: list[dict],
    test_set: list[dict],
    skill_name: str,
    num_workers: int,
    timeout: int,
    runs_per_query: int,
    trigger_threshold: float,
    model: str,
) -> tuple[dict, dict | None]:
    all_queries = train_set + test_set
    project_root = find_project_root()
    
    # Note: run_eval is now async, so this needs to be called with asyncio.run()
    # However, this refactoring assumes we keep run_loop as the main entry
    import asyncio
    
    all_results = asyncio.run(run_eval(
        eval_set=all_queries,
        skill_name=skill_name,
        description=current_description,
        num_workers=num_workers,
        timeout=timeout,
        project_root=project_root,
        runs_per_query=runs_per_query,
        trigger_threshold=trigger_threshold,
        model=model,
    ))

    train_queries_set = {q["query"] for q in train_set}
    train_result_list = [r for r in all_results["results"] if r["query"] in train_queries_set]
    test_result_list = [r for r in all_results["results"] if r["query"] not in train_queries_set]

    train_passed = sum(1 for r in train_result_list if r["pass"])
    train_total = len(train_result_list)
    train_results = {
        "results": train_result_list,
        "summary": {"passed": train_passed, "failed": train_total - train_passed, "total": train_total}
    }

    test_results = None
    if test_set:
        test_passed = sum(1 for r in test_result_list if r["pass"])
        test_total = len(test_result_list)
        test_results = {
            "results": test_result_list,
            "summary": {"passed": test_passed, "failed": test_total - test_passed, "total": test_total}
        }
        
    return train_results, test_results


def run_loop(
    eval_set: list[dict],
    skill_path: Path,
    description_override: str | None,
    num_workers: int,
    timeout: int,
    max_iterations: int,
    runs_per_query: int,
    trigger_threshold: float,
    holdout: float,
    model: str,
    verbose: bool,
    live_report_path: Path | None = None,
    log_dir: Path | None = None,
) -> dict:
    name, original_description, content = parse_skill_md(skill_path)
    current_description = description_override or original_description
    train_set, test_set = split_eval_set(eval_set, holdout) if holdout > 0 else (eval_set, [])
    history = []

    for iteration in range(1, max_iterations + 1):
        train_results, test_results = _run_iteration(
            iteration, current_description, train_set, test_set, name, 
            num_workers, timeout, runs_per_query, trigger_threshold, model
        )

        history.append({
            "iteration": iteration,
            "description": current_description,
            "train_passed": train_results["summary"]["passed"],
            "train_total": train_results["summary"]["total"],
            "train_results": train_results["results"],
            "test_passed": test_results["summary"]["passed"] if test_results else None,
            "test_total": test_results["summary"]["total"] if test_results else None,
            "test_results": test_results["results"] if test_results else None,
        })

        if live_report_path:
            live_report_path.write_text(generate_html({
                "original_description": original_description,
                "best_description": current_description,
                "iterations_run": len(history),
                "history": history,
            }, auto_refresh=True, skill_name=name), encoding="utf-8")

        if train_results["summary"]["failed"] == 0 or iteration == max_iterations:
            break

        current_description = improve_description(
            name, content, current_description, train_results,
            [{k: v for k, v in h.items() if not k.startswith("test_")} for h in history],
            model, None, log_dir, iteration
        )

    best = max(history, key=lambda h: h["test_passed"] if test_set else h["train_passed"])
    return {
        "best_description": best["description"],
        "history": history,
    }

def main():
    parser = argparse.ArgumentParser(description="Run eval + improve loop")
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--model", required=True)
    # ... rest of args ...
    args = parser.parse_args()
    
    eval_set = load_json(Path(args.eval_set))
    output = run_loop(eval_set, Path(args.skill_path), **vars(args))
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
