"""Record baseline and version-aware retrieval for selected questions."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from retrieval import embed, passages, retrieve
from versionlens import questions

PILOT_IDS = {"Q02", "Q03", "Q17", "Q18", "Q21", "Q24"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--embedding-model", default="nomic-embed-text")
    parser.add_argument("--corpus", type=Path, default=Path("data/pilot_corpus.jsonl"))
    parser.add_argument("--coverage", type=Path, help="JSON file listing evidence_ready_ids")
    parser.add_argument("--ids", nargs="+", help="Question IDs; omit for the six-case pilot")
    parser.add_argument("--all", action="store_true", help="Retrieve for all 24 questions")
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--output", type=Path, default=Path("results/retrieval_pilot.json"))
    args = parser.parse_args()
    if args.all and args.ids:
        parser.error("Choose --all or --ids, not both")
    if args.top_k < 1:
        parser.error("--top-k must be positive")
    corpus = passages(args.corpus)
    covered_ids = None
    if args.coverage:
        covered_ids = set(json.loads(args.coverage.read_text(encoding="utf-8"))["evidence_ready_ids"])
    dataset = questions()
    selected_ids = {row["id"] for row in dataset} if args.all else set(args.ids or PILOT_IDS)
    unknown = selected_ids - {row["id"] for row in dataset}
    if unknown:
        parser.error(f"Unknown question IDs: {', '.join(sorted(unknown))}")
    selected = [row for row in dataset if row["id"] in selected_ids]
    vectors = embed([row["summary"] for row in corpus] + [row["query"] for row in selected],
                    args.base_url, args.embedding_model)
    corpus_vectors = vectors[:len(corpus)]
    query_vectors = vectors[len(corpus):]
    records = []
    for row, vector in zip(selected, query_vectors):
        records.append({
            "id": row["id"],
            "query": row["query"],
            "evidence_ready": row["id"] in covered_ids if covered_ids is not None else None,
            "baseline": retrieve(row["query"], vector, corpus, corpus_vectors, "baseline", args.top_k),
            "version_aware": retrieve(row["query"], vector, corpus, corpus_vectors, "version_aware", args.top_k),
        })
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "corpus": str(args.corpus),
        "coverage": str(args.coverage) if args.coverage else None,
        "embedding_model": args.embedding_model,
        "top_k": args.top_k,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved retrieval for {len(records)} questions to {args.output}")


if __name__ == "__main__":
    main()
