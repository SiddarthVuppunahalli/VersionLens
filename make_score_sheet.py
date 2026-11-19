"""Create a human-review sheet from a completed six-question RAG run."""

import argparse
import csv
import json
from pathlib import Path

LABELS = Path(__file__).resolve().parent / "data" / "pilot_labels.jsonl"
FIELDS = (
    "model", "configuration", "id", "source", "model_called", "expected_action",
    "acceptable_answer", "must_not", "required_source", "retrieved_ids", "response",
    "action_correct_0_or_1", "migration_score_0_to_2", "citation_correct_0_or_1", "review_notes",
)


def load_labels() -> dict:
    with LABELS.open(encoding="utf-8") as handle:
        labels = [json.loads(line) for line in handle if line.strip()]
    if len(labels) != 6 or any(row["review_status"] != "approved" for row in labels):
        raise ValueError("Six approved pilot labels are required before scoring")
    return {row["id"]: row for row in labels}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, default=Path("results/rag_pilot.json"))
    parser.add_argument("--output", type=Path, default=Path("results/pilot_score_sheet.csv"))
    args = parser.parse_args()
    labels = load_labels()
    run = json.loads(args.run.read_text(encoding="utf-8"))
    records = run["records"]
    if not records or any(row["id"] not in labels for row in records):
        raise ValueError("Run contains no pilot records or an unknown question ID")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in records:
            label = labels[record["id"]]
            writer.writerow({
                "model": record["model"], "configuration": record["configuration"],
                "id": record["id"], "source": record["source"],
                "model_called": record["model_called"],
                "expected_action": label["expected_action"],
                "acceptable_answer": label["acceptable_answer"],
                "must_not": label["must_not"],
                "required_source": label["required_source"] or "",
                "retrieved_ids": ", ".join(record["retrieved_ids"]),
                "response": record["response"] or "",
            })
    print(f"Saved {len(records)} unscored rows to {args.output}")


if __name__ == "__main__":
    main()
