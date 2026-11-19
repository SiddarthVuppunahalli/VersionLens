"""Build a portable, read-only evidence packet for presentation Q&A."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "PRESENTATION_EVIDENCE.md", "README.md", "IMPLEMENTATION.md",
    "data/questions.jsonl", "data/pilot_labels.jsonl", "data/expanded_labels.jsonl",
    "data/expanded_corpus.jsonl", "data/expanded_coverage.json",
    "results/behavior_validation.json", "results/retrieval_expanded.json",
    "results/rag_expanded.json", "results/expanded_score_sheet_reviewed.csv",
    "results/expanded_scores_reviewed.jsonl", "results/expanded_scored.json",
    "run_behavior_tests.py", "tests/behavior_cases.py", "run_retrieval.py",
    "retrieval.py", "run_rag.py", "run_models.py", "versionlens.py",
    "requirements/pandas15.txt", "requirements/pandas20.txt",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, help="Optional original project proposal PDF")
    parser.add_argument("--output", type=Path, default=ROOT / "presentation_evidence.zip")
    args = parser.parse_args()
    sources = [(ROOT / name, name) for name in FILES]
    if args.proposal:
        sources.append((args.proposal, "original_project_proposal.pdf"))
    missing = [str(path) for path, _ in sources if not path.is_file()]
    if missing:
        parser.error("Missing evidence files: " + ", ".join(missing))
    manifest = {name: hashlib.sha256(path.read_bytes()).hexdigest() for path, name in sources}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, name in sources:
            archive.write(path, name)
        archive.writestr("manifest.json", json.dumps({"sha256": manifest}, indent=2) + "\n")
    print(f"Packed {len(sources)} evidence files into {args.output}")


if __name__ == "__main__":
    main()
