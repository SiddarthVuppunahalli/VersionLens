"""Check the larger-run safety boundary without calling a model."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_retrieval

from make_score_sheet import load_labels

ROOT = Path(__file__).resolve().parents[1]


class ExpandedRunTests(unittest.TestCase):
    def test_thirteen_approved_labels(self):
        labels = load_labels([ROOT / "data" / "pilot_labels.jsonl", ROOT / "data" / "expanded_labels.jsonl"])
        self.assertEqual(len(labels), 13)
        self.assertEqual(labels["Q10"]["fixture_id"], "Q10")

    def test_all_questions_retrieved_with_coverage_flags(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "retrieval.json"
            arguments = ["run_retrieval.py", "--all", "--corpus", str(ROOT / "data" / "expanded_corpus.jsonl"),
                         "--coverage", str(ROOT / "data" / "expanded_coverage.json"), "--output", str(output)]
            with patch.object(sys, "argv", arguments), patch.object(run_retrieval, "embed", side_effect=lambda texts, *_: [[1.0, 0.0] for _ in texts]):
                run_retrieval.main()
            records = json.loads(output.read_text(encoding="utf-8"))["records"]
            self.assertEqual(len(records), 24)
            self.assertTrue(next(row for row in records if row["id"] == "Q10")["evidence_ready"])
            self.assertFalse(next(row for row in records if row["id"] == "Q11")["evidence_ready"])

    def test_evidence_gap_skips_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            retrieval = Path(temporary) / "retrieval.json"
            output = Path(temporary) / "rag.json"
            retrieval.write_text(json.dumps({"records": [{
                "id": "Q11", "query": "How should I migrate groupby squeeze?",
                "evidence_ready": False, "baseline": [], "version_aware": [],
            }]}), encoding="utf-8")
            subprocess.run([
                sys.executable, str(ROOT / "run_rag.py"), "--models", "unavailable-model",
                "--retrieval", str(retrieval), "--output", str(output),
            ], cwd=ROOT, check=True, capture_output=True, text=True)
            records = json.loads(output.read_text(encoding="utf-8"))["records"]
            self.assertEqual(len(records), 2)
            self.assertTrue(all(row["source"] == "evidence_gap" and not row["model_called"] for row in records))


if __name__ == "__main__":
    unittest.main()
