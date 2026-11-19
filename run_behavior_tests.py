"""Compare trusted fixture outputs across pandas 1.5.3 and 2.0.3."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "tests" / "behavior_cases.py"


def run_fixture(python_path: Path, version: str) -> dict:
    completed = subprocess.run(
        [str(python_path), str(FIXTURES), "--target", version],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )
    return json.loads(completed.stdout)


def compare(old: dict, new: dict) -> dict:
    case_ids = sorted(set(old["cases"]) | set(new["cases"]))
    cases = {}
    for case_id in case_ids:
        old_case = old["cases"].get(case_id)
        new_case = new["cases"].get(case_id)
        equivalent = bool(old_case and new_case and old_case["observed"] == new_case["observed"])
        record = {
            "equivalent": equivalent,
            "original": old_case["observed"] if old_case else None,
            "migration": new_case["observed"] if new_case else None,
        }
        if case_id == "Q02" and old_case and new_case:
            record["negative_control_differs"] = old_case["observed"] != new_case["negative_control"]
        cases[case_id] = record
    passed = all(row["equivalent"] for row in cases.values()) and cases.get("Q02", {}).get("negative_control_differs", False)
    api_transition = all(
        old["removed_api_available"][api] and not new["removed_api_available"][api]
        for api in ("Series.append", "DataFrame.iteritems", "Int64Index", "Index.is_monotonic")
    )
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "environments": {
            "original": {key: old[key] for key in ("python_version", "numpy_version", "pandas_version")},
            "migration": {key: new[key] for key in ("python_version", "numpy_version", "pandas_version")},
        },
        "removed_api_transition_confirmed": api_transition,
        "cases": cases,
        "passed": passed and api_transition,
        "note": "Trusted fixed fixtures only; no user or model code is executed.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python15", type=Path, default=ROOT / ".venv15" / "Scripts" / "python.exe")
    parser.add_argument("--python20", type=Path, default=ROOT / ".venv20" / "Scripts" / "python.exe")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "behavior_validation.json")
    args = parser.parse_args()
    old = run_fixture(args.python15, "1.5.3")
    new = run_fixture(args.python20, "2.0.3")
    report = compare(old, new)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for case_id, row in report["cases"].items():
        print(f"{case_id}: equivalent={row['equivalent']}")
    print(f"Q02 negative control differs={report['cases']['Q02']['negative_control_differs']}")
    print(f"Removed APIs confirmed={report['removed_api_transition_confirmed']}")
    print(f"Saved {args.output}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
