"""Run one question or save prototype outputs for all 24 questions."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from versionlens import answer, questions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", help="Question ID, for example Q02")
    parser.add_argument("--query", help="A custom question")
    parser.add_argument("--all", action="store_true", help="Save outputs and routing metrics")
    parser.add_argument("--output", type=Path, default=Path("results/prototype.json"))
    args = parser.parse_args()
    if args.all:
        rows = questions()
        outputs = [{"id": row["id"], "expected_action": row["expected_action"], **answer(row["query"])} for row in rows]
        matching = sum(row["action"] == row["expected_action"] for row in outputs)
        report = {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "system": "deterministic prototype (no LLM)",
            "dataset_size": len(rows),
            "dataset_label_status": "draft; labels require manual review",
            "metrics": {
                "routing_matches_draft_labels": matching,
                "routing_match_rate": matching / len(rows),
                "action_counts": dict(Counter(row["action"] for row in outputs)),
                "migration_correctness": None,
                "citation_correctness": None,
                "behavioral_equivalence": None,
            },
            "outputs": outputs,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Saved {len(rows)} outputs to {args.output}")
        print(f"Routing matches draft labels: {matching}/{len(rows)}; this is not migration accuracy.")
    else:
        query = args.query
        if args.id:
            query = next((row["query"] for row in questions() if row["id"] == args.id), None)
            if query is None:
                parser.error(f"Unknown question ID: {args.id}")
        if not query:
            parser.error("Provide --id, --query, or --all")
        print(json.dumps(answer(query), indent=2))


if __name__ == "__main__":
    main()
