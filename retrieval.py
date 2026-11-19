"""Pilot semantic baseline and version-aware hybrid retrieval over fixed summaries."""

import ast
import json
import math
import re
import urllib.request
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "data" / "pilot_corpus.jsonl"


def passages() -> list[dict]:
    with CORPUS.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate passage ID")
    return rows


def embed(texts: list[str], base_url: str, model: str = "nomic-embed-text") -> list[list[float]]:
    payload = json.dumps({"model": model, "input": texts, "truncate": False}).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        vectors = json.load(response)["embeddings"]
    if len(vectors) != len(texts):
        raise ValueError("Embedding count does not match input count")
    return vectors


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Embedding dimensions differ")
    magnitude = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / magnitude if magnitude else 0.0


def api_tokens(query: str) -> set[str]:
    """Parse simple dotted calls inside prose without executing code."""
    found = set()
    candidates = re.findall(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\([^()]*\)", query)
    for candidate in candidates:
        try:
            tree = ast.parse(candidate, mode="eval")
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                found.add(node.func.attr.lower())
    return found


def retrieve(query: str, query_vector: list[float], corpus: list[dict],
             corpus_vectors: list[list[float]], configuration: str, top_k: int = 2) -> list[dict]:
    if configuration not in ("baseline", "version_aware"):
        raise ValueError("Unknown retrieval configuration")
    if len(corpus) != len(corpus_vectors):
        raise ValueError("Corpus and embeddings differ in length")
    words = set(re.findall(r"[a-z_]+", query.lower()))
    calls = api_tokens(query)
    scored = []
    for passage, vector in zip(corpus, corpus_vectors):
        if configuration == "version_aware" and passage["version"] != "2.0.3":
            continue
        semantic = cosine(query_vector, vector)
        if configuration == "baseline":
            score = semantic
        else:
            passage_words = set(re.findall(r"[a-z_]+", (passage["api"] + " " + passage["summary"]).lower()))
            lexical = len(words & passage_words) / max(1, len(words))
            api_match = bool(calls & set(passage["api"].split()))
            score = 0.7 * semantic + 0.2 * lexical + 0.1 * api_match
        scored.append({"id": passage["id"], "score": round(score, 6), **passage})
    return sorted(scored, key=lambda row: (-row["score"], row["id"]))[:top_k]
