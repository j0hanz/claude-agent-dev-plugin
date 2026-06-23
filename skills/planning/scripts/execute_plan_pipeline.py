import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    name = args.name

    scripts_dir = Path(os.path.abspath(__file__)).parent
    plan_dir = Path("plan").resolve()

    spec_path = plan_dir / f"{name}.specs.md"
    plan_path = plan_dir / f"{name}.plan.md"

    # Pre-flight: both artifacts must already exist (Step 2 scaffolds + authors them)
    for path_obj in (spec_path, plan_path):
        if not path_obj.exists():
            print(f"[!] {path_obj} not found. Run scaffold.py and author it first.")
            sys.exit(1)

    # 1. Validate spec
    print("[*] Validating Spec...")
    res_spec = subprocess.run(
        ["python", str(scripts_dir / "validate.py"), name, "--spec"]
    )
    if res_spec.returncode != 0:
        print("\n[!] Spec validation failed. Please fix the spec file and re-run.")
        sys.exit(res_spec.returncode)

    # 2. Sync Satisfies: fields from spec into plan
    print("[*] Syncing...")
    res_sync = subprocess.run(["python", str(scripts_dir / "sync.py"), str(spec_path)])
    if res_sync.returncode != 0:
        print("\n[!] Sync failed. Fix the spec file and re-run.")
        sys.exit(res_sync.returncode)

    # 3. Validate plan
    print("[*] Validating Plan...")
    res_plan = subprocess.run(
        ["python", str(scripts_dir / "validate.py"), name, "--plan"]
    )
    if res_plan.returncode != 0:
        print("\n[!] Plan validation failed. Please fix the plan file and re-run.")
        sys.exit(res_plan.returncode)

    # 4. Cross-validate spec ↔ plan traceability
    print("[*] Cross-Validating...")
    res_cross = subprocess.run(
        ["python", str(scripts_dir / "validate.py"), name, "--cross"]
    )
    if res_cross.returncode != 0:
        print("\n[!] Cross validation failed.")
        sys.exit(res_cross.returncode)

    print("\n[+] Pipeline completed successfully. All validations passed.")


if __name__ == "__main__":
    main()
