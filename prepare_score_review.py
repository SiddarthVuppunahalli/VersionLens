"""Join manual score judgments to a Colab score sheet.

This script copies judgments; it does not grade model text.
"""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", type=Path, default=Path("results/expanded_score_sheet.csv"))
    parser.add_argument("--proposals", type=Path, default=Path("results/expanded_scores_reviewed.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("results/expanded_score_sheet_reviewed.csv"))
    args = parser.parse_args()
    with args.proposals.open(encoding="utf-8") as handle:
        proposals = [json.loads(line) for line in handle if line.strip()]
    key = lambda row: (row["model"], row["configuration"], row["id"])
    by_key = {key(row): row for row in proposals}
    if len(by_key) != len(proposals):
        raise ValueError("Duplicate score proposal")
    with args.sheet.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    eligible = {key(row) for row in rows if row["source"] == "model"}
    if set(by_key) != eligible:
        raise ValueError(f"Proposals do not match model-backed labeled rows: missing={eligible - set(by_key)}, extra={set(by_key) - eligible}")
    for row in rows:
        proposal = by_key.get(key(row))
        if not proposal:
            continue
        if "action_correct" in proposal:
            row["action_correct_0_or_1"] = int(proposal["action_correct"])
        if "migration_score" in proposal:
            row["migration_score_0_to_2"] = proposal["migration_score"]
        if proposal.get("citation_correct") is not None:
            row["citation_correct_0_or_1"] = int(proposal["citation_correct"])
        row["review_notes"] = proposal["note"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows, including {len(proposals)} model judgments, to {args.output}")


if __name__ == "__main__":
    main()
