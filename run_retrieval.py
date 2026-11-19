"""Record baseline and version-aware retrieval for the six pilot questions."""

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
    parser.add_argument("--output", type=Path, default=Path("results/retrieval_pilot.json"))
    args = parser.parse_args()
    corpus = passages()
    selected = [row for row in questions() if row["id"] in PILOT_IDS]
    vectors = embed([row["summary"] for row in corpus] + [row["query"] for row in selected],
                    args.base_url, args.embedding_model)
    corpus_vectors = vectors[:len(corpus)]
    query_vectors = vectors[len(corpus):]
    records = []
    for row, vector in zip(selected, query_vectors):
        records.append({
            "id": row["id"],
            "query": row["query"],
            "baseline": retrieve(row["query"], vector, corpus, corpus_vectors, "baseline"),
            "version_aware": retrieve(row["query"], vector, corpus, corpus_vectors, "version_aware"),
        })
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "corpus": "data/pilot_corpus.jsonl",
        "embedding_model": args.embedding_model,
        "top_k": 2,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved retrieval for {len(records)} questions to {args.output}")


if __name__ == "__main__":
    main()
