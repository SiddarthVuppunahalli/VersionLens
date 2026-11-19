"""Validate owner-approved judgments and save reproducible expanded-run totals."""

import collections
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from make_score_sheet import load_labels

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RUN = RESULTS / "rag_expanded.json"
RETRIEVAL = RESULTS / "retrieval_expanded.json"
SHEET = RESULTS / "expanded_score_sheet.csv"
JUDGMENTS = RESULTS / "expanded_scores_reviewed.jsonl"
REVIEWED_SHEET = RESULTS / "expanded_score_sheet_reviewed.csv"
OUTPUT = RESULTS / "expanded_scored.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    labels = load_labels([ROOT / "data" / "pilot_labels.jsonl", ROOT / "data" / "expanded_labels.jsonl"])
    run = json.loads(RUN.read_text(encoding="utf-8"))
    retrieval = json.loads(RETRIEVAL.read_text(encoding="utf-8"))
    judgments = [json.loads(line) for line in JUDGMENTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    key = lambda row: (row["model"], row["configuration"], row["id"])
    by_key = {key(row): row for row in judgments}
    if len(by_key) != len(judgments):
        raise ValueError("Duplicate reviewed judgment")
    records = run["records"]
    model_records = [row for row in records if row["source"] == "model" and row["id"] in labels]
    if len(records) != 96 or len(retrieval["records"]) != 24 or len(model_records) != 40:
        raise ValueError("Expanded run is incomplete")
    if {key(row) for row in model_records} != set(by_key):
        raise ValueError("Reviewed judgments do not match the model-backed labeled records")
    if any(row.get("error") for row in records):
        raise ValueError("Run contains an error")
    expected_passage = {
        "Q02": "p20_concat_index", "Q03": "p20_iteritems_removed", "Q04": "p20_int64index",
        "Q05": "p20_iso_week", "Q06": "p20_monotonic", "Q07": "p20_to_csv_terminator",
        "Q08": "p20_set_axis", "Q09": "p20_read_csv_bad_lines", "Q10": "p20_read_csv_squeeze",
        "Q17": "p20_groupby_mean", "Q22": "p20_append_removed",
    }
    retrieval_by_id = {row["id"]: row for row in retrieval["records"]}
    if len(retrieval_by_id) != 24:
        raise ValueError("Duplicate retrieval question ID")
    retrieval_hits = {
        configuration: sum(expected in {passage["id"] for passage in retrieval_by_id[case_id][configuration]}
                           for case_id, expected in expected_passage.items())
        for configuration in ("baseline", "version_aware")
    }
    grouped = collections.defaultdict(list)
    for row in judgments:
        grouped[(row["model"], row["configuration"])].append(row)
    summary = []
    for (model, configuration), rows in grouped.items():
        migrations = [row for row in rows if row["id"] in {f"Q{i:02d}" for i in range(2, 11)}]
        unchanged = [row for row in rows if row["id"] == "Q17"]
        if len(migrations) != 9 or len(unchanged) != 1:
            raise ValueError("Missing migration or unchanged-code judgment")
        summary.append({
            "model": model,
            "configuration": configuration,
            "migration_points": sum(row["migration_score"] for row in migrations),
            "migration_points_possible": 18,
            "unchanged_action_correct": int(unchanged[0]["action_correct"]),
            "required_citations_present": sum(row["citation_correct"] is not None for row in migrations),
            "required_citations_possible": 9,
            "cited_sources_correct": sum(row["citation_correct"] is True for row in migrations),
            "cited_sources_checked": sum(row["citation_correct"] is not None for row in migrations),
        })
    preflight_ids = ("Q18", "Q21", "Q24")
    for case_id in preflight_ids:
        case_rows = [row for row in records if row["id"] == case_id]
        if len(case_rows) != 4 or any(row["source"] != "preflight" or row["model_called"] or row["action"] != labels[case_id]["expected_action"] for row in case_rows):
            raise ValueError(f"Reviewed preflight case failed: {case_id}")
    report = {
        "status": "project_owner_approved",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": {name: digest(path) for name, path in (
            ("rag_expanded.json", RUN), ("retrieval_expanded.json", RETRIEVAL),
            ("expanded_score_sheet.csv", SHEET), ("expanded_scores_reviewed.jsonl", JUDGMENTS),
            ("expanded_score_sheet_reviewed.csv", REVIEWED_SHEET),
        )},
        "evaluation_set": sorted(labels),
        "routing": dict(collections.Counter(row["source"] for row in records)),
        "retrieval_diagnostic": {
            "expected_passage_by_question": expected_passage,
            "top_two_hits": retrieval_hits,
            "questions_checked": len(expected_passage),
            "note": "A manually selected target passage was checked in the top two results; this is a corpus diagnostic, not model-answer correctness.",
        },
        "model_backed_scores": judgments,
        "summary": summary,
        "shared_preflight": {"ids": list(preflight_ids), "correct_actions": 3, "total_actions": 3,
                             "note": "Shared deterministic preflight responses are excluded from model averages."},
        "limitations": [
            "Migration scores cover nine fixed questions, not all 24 dataset questions.",
            "The corpus contains 13 curated summaries, not full documentation passages.",
            "Citation coverage is separate from correctness among citations supplied; no citation is recorded as null.",
            "Behavior fixtures validate trusted reference migrations, not model-generated code.",
            "Preflight and evidence-gap responses are system behavior, not model successes.",
        ],
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved reviewed scores for {len(judgments)} model-backed answers to {OUTPUT}")


if __name__ == "__main__":
    main()
