import json
import unittest
from unittest.mock import patch

from versionlens import preflight, questions, retrieve_evidence, validate_model_answer
from run_models import call_ollama


class PipelineTests(unittest.TestCase):
    def test_preflight_handles_known_guardrail_cases(self):
        rows = {row["id"]: row for row in questions()}
        for question_id, action in (("Q18", "clarify"), ("Q21", "decline"),
                                    ("Q23", "ignore_injection"), ("Q24", "refuse_execution")):
            with self.subTest(question_id=question_id):
                self.assertEqual(preflight(rows[question_id]["query"])["action"], action)
        self.assertIsNone(preflight(rows["Q02"]["query"]))

    def test_evidence_is_version_tagged_and_official(self):
        query = next(row["query"] for row in questions() if row["id"] == "Q02")
        evidence = retrieve_evidence(query)
        self.assertEqual([item["id"] for item in evidence], ["append_removed", "concat_indices"])
        self.assertTrue(all(item["version"] == "2.0.3" for item in evidence))
        self.assertTrue(all(item["url"].startswith("https://pandas.pydata.org/") for item in evidence))

    def test_model_request_contains_evidence_and_disables_thinking(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                pass

            def read(self):
                return b'{"message":{"content":"answer"},"done_reason":"stop"}'

        captured = {}

        def fake_urlopen(request, timeout):
            captured.update(json.loads(request.data))
            return FakeResponse()

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            body, _ = call_ollama("http://localhost:11434", "test-model", "s1.append(s2)", 5, 700,
                                  retrieve_evidence("s1.append(s2)"))
        self.assertEqual(body["message"]["content"], "answer")
        self.assertFalse(captured["think"])
        self.assertEqual(captured["options"]["num_predict"], 700)
        self.assertIn("pandas.pydata.org", captured["messages"][1]["content"])

    def test_index_preservation_check_rejects_contradictory_code(self):
        query = next(row["query"] for row in questions() if row["id"] == "Q02")
        evidence = retrieve_evidence(query)
        bad = "combined = pd.concat([s1, s2], ignore_index=True)"
        self.assertIn("discards", validate_model_answer(query, bad, evidence))
        good = ("combined = pd.concat([s1, s2], ignore_index=False)\n"
                + evidence[1]["url"])
        self.assertIsNone(validate_model_answer(query, good, evidence))


if __name__ == "__main__":
    unittest.main()
