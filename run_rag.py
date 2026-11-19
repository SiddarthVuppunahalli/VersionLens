"""Compare two retrieval configurations with identical local generator settings."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from run_models import call_ollama
from versionlens import preflight


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieval", type=Path, default=Path("results/retrieval_pilot.json"))
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--num-predict", type=int, default=700)
    parser.add_argument("--output", type=Path, default=Path("results/rag_pilot.json"))
    args = parser.parse_args()
    retrieval_run = json.loads(args.retrieval.read_text(encoding="utf-8"))
    records = []
    for model in args.models:
        for configuration in ("baseline", "version_aware"):
            for row in retrieval_run["records"]:
                guard = preflight(row["query"])
                evidence = row[configuration]
                print(f"{model} {configuration} {row['id']}", flush=True)
                record = {
                    "model": model, "configuration": configuration, "id": row["id"],
                    "retrieved_ids": [item["id"] for item in evidence],
                    "retrieved_sources": [item["url"] for item in evidence],
                }
                if guard:
                    record.update({"response": guard["response"], "source": "preflight",
                                   "model_called": False, "action": guard["action"],
                                   "latency_seconds": 0, "done_reason": None, "error": None})
                else:
                    try:
                        body, seconds = call_ollama(args.base_url, model, row["query"], 300,
                                                    args.num_predict, evidence)
                        response = body["message"].get("content", "")
                        record.update({"response": response, "source": "model", "model_called": True,
                                       "action": None, "latency_seconds": seconds,
                                       "done_reason": body.get("done_reason"),
                                       "error": None if response.strip() else "empty answer"})
                    except (OSError, KeyError, ValueError) as exc:
                        record.update({"response": None, "source": "model", "model_called": True,
                                       "action": None, "latency_seconds": None,
                                       "done_reason": None, "error": str(exc)})
                records.append(record)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps({
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "retrieval_file": str(args.retrieval),
                    "labels_review_status": "approved; no scores computed",
                    "generation": f"temperature=0, seed=42, think=false, num_predict={args.num_predict}",
                    "records": records,
                }, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
