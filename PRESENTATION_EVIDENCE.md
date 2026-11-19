# VersionLens presentation evidence

Open this guide during Q&A. Each row points to the record behind a claim in the presentation. The [reviewed expanded score record](results/expanded_scored.json) also stores SHA-256 hashes of the uploaded run files and reviewed judgments.

| Claim you may need to show | Open this evidence | What it establishes |
| --- | --- | --- |
| The evaluation set has 24 author-written questions | [Question set](data/questions.jsonl) | Q01–Q24 and their categories. These are project-authored prompts, not a sampled external benchmark. |
| Thirteen gold labels were approved | [Pilot labels](data/pilot_labels.jsonl) and [expanded labels](data/expanded_labels.jsonl) | Six pilot labels plus seven Q04–Q10 labels, each marked `approved`. The remaining questions are not all scored. |
| The corpus has 13 curated summaries from official pandas pages | [Expanded corpus](data/expanded_corpus.jsonl) | Each record has a version, API, section, official URL, and short summary. It is not a full documentation index. |
| Eleven questions have relevant evidence in that corpus | [Coverage declaration](data/expanded_coverage.json) and [retrieval run](results/retrieval_expanded.json) | Eleven IDs are marked evidence-ready. This means a relevant summary exists in the corpus, not that every retrieved answer is correct. |
| Nine fixed migration cases passed across versions | [Behavior report](results/behavior_validation.json), [fixture code](tests/behavior_cases.py), and [runner](run_behavior_tests.py) | Q02–Q10 reference migrations produced matching declared snapshots in pinned pandas 1.5.3 and 2.0.3 environments. Q05 compares ISO week values but permits a dtype difference. Q09 does not grade warning text. Model-generated code was not executed. |
| Two open models and two retrieval configurations were compared | [Generation run](results/rag_expanded.json), [retrieval runner](run_retrieval.py), [RAG runner](run_rag.py), and [Ollama request settings](run_models.py) | Qwen3 1.7B and Qwen2.5 Coder 1.5B received the same questions and generation settings under semantic baseline and version-aware retrieval. |
| The full run has 96 records: 44 model, 28 preflight, 24 evidence gap | [Reviewed score record](results/expanded_scored.json) and [raw generation run](results/rag_expanded.json) | Routing counts are separated so deterministic answers do not inflate model scores. |
| Migration scores are 16/18 and 13/18 for Qwen3, 11/18 and 10/18 for Qwen Coder | [Reviewed score sheet](results/expanded_score_sheet_reviewed.csv), [per-answer judgments](results/expanded_scores_reviewed.jsonl), and [summary](results/expanded_scored.json) | Project-owner-approved judgments over nine migration questions, Q02–Q10. The maximum is two points per case. |
| Target passage appears in the top two for 10/11 baseline and 11/11 version-aware | [Retrieval diagnostic](results/expanded_scored.json) and [raw retrieval](results/retrieval_expanded.json) | The diagnostic lists the selected passage ID for each of 11 covered questions. This is retrieval evidence, not migration correctness. |
| Qwen3 cited supporting official sources in 7/9 baseline and 6/9 version-aware migration answers; Qwen Coder cited none | [Reviewed score record](results/expanded_scored.json) and [raw answers](results/rag_expanded.json) | Citation coverage is separate from correctness among citations supplied. These counts apply only to the nine scored migration questions. |
| Known ambiguity, scope, and unsafe cases received deterministic responses | [Preflight rules](versionlens.py), [generation run](results/rag_expanded.json), and [approved labels](data/pilot_labels.jsonl) | Q18, Q21, and Q24 passed their approved action labels through shared preflight. These are system results, not model successes or a general safety guarantee. |
| The larger tool-assisted assistant remains planned | [README](README.md) and [implementation plan](IMPLEMENTATION.md) | Current retrieval uses a small curated corpus and simple API-call parsing. Broader indexing, richer code analysis, and constrained validation of selected generated migrations remain future work. |

## Fast Q&A examples

- **A migration that runs but changes behavior:** open Q02 in [raw answers](results/rag_expanded.json). Qwen Coder uses `ignore_index=True` while claiming to preserve indices. The [behavior report](results/behavior_validation.json) includes a negative control showing that this resets labels.
- **A partial migration:** open Q03 in the [reviewed score sheet](results/expanded_score_sheet_reviewed.csv). Some answers write `df.items` without `()`, or invent output. The reviewed notes explain partial credit.
- **Why better retrieval did not guarantee better answers:** show `retrieval_diagnostic` beside `summary` in the [reviewed score record](results/expanded_scored.json). The version-aware path had 11/11 target-passage hits but lower migration points in this small run.
- **Clarification and refusal:** open Q18, Q21, and Q24 in [raw answers](results/rag_expanded.json). Their `source` is `preflight` and `model_called` is `false`.

## Recheck locally

```powershell
python run_behavior_tests.py
python -m unittest discover -s tests -v
python finalize_expanded_scores.py
```

The first command needs the two pinned local environments described in the [README](README.md). The other commands use the saved files and standard project setup. Do not rerun the Ollama comparison immediately before presenting unless you intend to create a new experiment.
