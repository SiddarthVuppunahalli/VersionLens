import unittest

from make_score_sheet import load_labels
from retrieval import api_tokens, cosine, passages, retrieve


class RetrievalTests(unittest.TestCase):
    def test_corpus_metadata(self):
        rows = passages()
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["version"] for row in rows}, {"1.5.3", "2.0.3"})
        self.assertTrue(all(row["url"].startswith("https://pandas.pydata.org/") for row in rows))

    def test_pilot_labels_are_approved_and_distinct(self):
        labels = load_labels()
        self.assertEqual(set(labels), {"Q02", "Q03", "Q17", "Q18", "Q21", "Q24"})
        self.assertEqual(labels["Q02"]["fixture_id"], "Q02")

    def test_ast_extracts_simple_api_call(self):
        self.assertIn("append", api_tokens("Migrate combined = s1.append(s2) to pandas 2.0"))
        self.assertIn("iteritems", api_tokens("Why does df.iteritems() fail?"))

    def test_version_aware_filter_excludes_older_docs(self):
        rows = passages()
        vectors = [[1.0, 0.0] for _ in rows]
        baseline = retrieve("s1.append(s2)", [1.0, 0.0], rows, vectors, "baseline")
        aware = retrieve("s1.append(s2)", [1.0, 0.0], rows, vectors, "version_aware")
        self.assertEqual(len(baseline), 2)
        self.assertTrue(all(row["version"] == "2.0.3" for row in aware))
        self.assertTrue(cosine([1, 0], [1, 0]) == 1.0)


if __name__ == "__main__":
    unittest.main()
