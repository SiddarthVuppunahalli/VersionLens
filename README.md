# VersionLens

VersionLens is a version-aware API migration copilot for short pandas code snippets. It is designed to help users migrate code from pandas 1.5.3 to pandas 2.0.3 with minimal changes, an explanation of each change, and citations to the relevant official documentation.

## Research question

Does version-aware retrieval combined with code analysis and constrained validation improve migration accuracy and citation quality compared with standard semantic retrieval-augmented generation (RAG)?

## Scope

VersionLens will accept a pandas code snippet, error message, or migration question. It will aim to:

- identify version-related API changes;
- produce a minimal pandas 2.0.3-compatible migration;
- explain why each change is needed;
- cite official, version-appropriate pandas documentation;
- ask for missing context instead of guessing; and
- decline unsupported or unsafe requests.

The project is limited to short pandas snippets and the pandas 1.5.3-to-2.0.3 transition. It will not migrate entire repositories or support other libraries.

## Systems compared

1. **Baseline semantic RAG:** Retrieves semantically similar passages from a combined documentation collection without explicit version filtering or code-analysis tools.
2. **Version-aware assistant:** Uses source and target versions, version-filtered hybrid retrieval, Python AST analysis, and allow-listed validation tests. It can clarify or abstain when evidence is insufficient.

Both systems will use the same LLM and generation settings.

## Evaluation

The benchmark contains 24 drafted queries covering migrations, unchanged code, missing context, unsupported requests, and adversarial inputs. Before running either system, the project author will manually label each case with its category, expected response, acceptable migration, supporting official documentation, and applicable tests. The evaluated model will not grade its own output.

### Migration correctness

Each response will receive a fixed score based on the documented API change, intended behavior, and relevant test results:

- **0 - Incorrect:** The migration is wrong, unsupported, or changes the intended behavior.
- **1 - Partially correct:** The response identifies the relevant change but is incomplete or requires correction.
- **2 - Fully correct:** The migration is supported by the documentation and preserves the intended behavior for the defined case.

### Citation correctness

Each citation will be checked manually for both:

- the correct pandas version; and
- a passage that supports the associated claim.

Citation correctness will be reported as the fraction of citations that pass both checks.

### Execution and behavioral equivalence

Execution success and behavioral equivalence are separate results. Execution success means only that the migrated snippet runs without an exception.

For supported snippets, behavioral equivalence will compare the original code in pandas 1.5.3 with the migrated code in pandas 2.0.3 using identical fixed inputs. A test passes only when the outputs match the case's predeclared expectations for values, shape, index and column labels, ordering, and relevant dtypes or timezone behavior. Any permitted difference or numerical tolerance will be defined before evaluation.

Additional measures will include version grounding, appropriate clarification, unsupported-claim frequency, and safe handling of out-of-scope or adversarial requests.

## Safety

VersionLens will default to static analysis. Any validation will use predefined or allow-listed tests in isolated environments without filesystem, network, or shell access. User code, comments, and retrieved text will be treated as untrusted input.

## Documentation sources

- [pandas 1.5.3 documentation](https://pandas.pydata.org/pandas-docs/version/1.5.3/)
- [pandas 2.0.3 documentation](https://pandas.pydata.org/pandas-docs/version/2.0.3/)
- [pandas 2.0 release notes](https://pandas.pydata.org/docs/whatsnew/v2.0.0.html)

## Run the current prototype

Python 3.10 or newer is sufficient; the current scripts use only the standard library.

```powershell
python run_demo.py --id Q02
python run_demo.py --id Q18
python run_demo.py --id Q24
python run_demo.py --all
```

The last command writes all 24 responses and routing counts to `results/prototype.json`. The prototype uses verified response templates for a few cases and asks for clarification on others. It does not execute submitted code.

## Run cross-version behavior tests

These trusted fixtures compare Q02–Q10 under pandas 1.5.3 and 2.0.3. They cover append, iteritems, Int64Index, ISO week values, monotonicity, CSV line endings, set_axis assignment, bad-line CSV parsing, and one-column CSV squeezing. On Windows with Python 3.10 or 3.11:

```powershell
python -m venv .venv15
python -m venv .venv20
.\.venv15\Scripts\python.exe -m pip install -r requirements\pandas15.txt
.\.venv20\Scripts\python.exe -m pip install -r requirements\pandas20.txt
python run_behavior_tests.py
python -m unittest discover -s tests -v
```

The runner writes `results/behavior_validation.json`, including both environment versions and case snapshots. Q02 deliberately includes duplicate index labels and a wrong `ignore_index=True` negative control; the run fails if that wrong output is not distinguishable. Q05 compares ISO week values but does not require the result dtype to match. Q09 compares parsed rows but does not grade warning text. Only predefined fixtures run; this does not validate arbitrary submitted code or model-generated snippets.

## Compare open models

The model comparison runner calls a local [Ollama](https://ollama.com/download/windows) server. On a CPU-only Windows machine, start with small quantized, Apache-licensed models such as `qwen3:1.7b` and `qwen2.5-coder:1.5b`; larger models may be slow or require more memory. Download the models once:

```powershell
ollama pull qwen3:1.7b
ollama pull qwen2.5-coder:1.5b
python run_models.py --models qwen3:1.7b qwen2.5-coder:1.5b --ids Q02 Q18 Q21 Q24
```

The default `guarded` configuration handles known unsafe, out-of-scope, and missing-context cases before calling a model. It supplies a small curated set of version-tagged official pandas facts for supported migrations. A narrow output check verifies that the `s1.append(s2)` migration preserves indices and cites an official source; on failure, it serves a known safe template. The JSON keeps the raw `candidate_response`, `validation_failure`, and `source: validated_fallback` so model errors remain visible. Preflight records use `source: preflight` and `model_called: false`. This is a scoped prototype, not the full RAG system or a general-purpose sandbox.

The runner saves outputs, latency, finish reason, and generated-token count to `results/model_comparison.json`. It requests a final answer without a separate thinking trace and marks empty answers as errors. Run without `--ids` for all 24 questions. Use `--configuration raw --output results/raw_comparison.json` to reproduce the unguarded model-only comparison. Keep raw and guarded results separate: preflight answers are system behavior, not model successes. Human grading is still required. Ollama is optional. The scripts can also run in a Colab environment with an Ollama server available there.

## Six-question retrieval pilot

`data/pilot_labels.jsonl` contains user-approved labels for Q02, Q03, Q17, Q18, Q21, and Q24. They are not passed to the generator. `data/pilot_corpus.jsonl` contains six human-curated summaries of official pandas pages, each with a version, API, section, and URL. These summaries are a small pilot corpus, not a complete documentation index.

With Ollama running locally or in Colab, pull the open embedding model and run retrieval before generation:

```powershell
ollama pull nomic-embed-text
python run_retrieval.py --output results/retrieval_pilot.json
python run_rag.py --models qwen3:1.7b --retrieval results/retrieval_pilot.json --output results/rag_pilot.json
python make_score_sheet.py --run results/rag_pilot.json --output results/pilot_score_sheet.csv
```

The baseline ranks all corpus records by semantic embedding similarity. The version-aware path filters to pandas 2.0.3 and combines semantic similarity with token and parsed API-call matching. Both use the same corpus, embedding model, top-two passage budget, generator model, and generation settings. Both also share the same preflight rule for missing context, out-of-scope requests, and unsafe code; those records show `model_called: false`. The run files preserve retrieved passage IDs and URLs for inspection. The score sheet leaves correctness fields blank for human review; it does not score models automatically.

### Reviewed pilot outcome

The project owner reviewed the uploaded pilot run's scores. The [reviewed score record](results/pilot_scored.json) includes per-case judgments, source-file hashes, and limitations. Across the two model-backed migration questions (Q02 and Q03), Qwen3 scored 3/4 points with baseline retrieval and 4/4 with version-aware retrieval. Qwen 2.5 Coder scored 1/4 in both configurations. Qwen3 supplied supporting citations for both migration answers in both configurations; Qwen 2.5 Coder supplied none. All four model/configuration combinations answered the unchanged-code case correctly. The three clarification, scope, and unsafe-code cases were handled by the same preflight rules and are excluded from model averages. This small pilot does not establish a general performance advantage.

## Larger test run

The expanded corpus has 13 curated summaries from official pandas documentation. The project owner approved seven more gold labels (Q04–Q10), making 13 approved labels total. Nine migration cases (Q02–Q10) now have trusted cross-version fixtures. The 24-question retrieval run marks which questions have relevant curated evidence. For uncovered questions, the generation runner records an `evidence_gap` clarification and does not call a model. These responses should be reported separately from model results.

With Ollama and `nomic-embed-text` available, run:

```powershell
python run_behavior_tests.py
python -m unittest discover -s tests -v
python run_retrieval.py --all --corpus data/expanded_corpus.jsonl --coverage data/expanded_coverage.json --output results/retrieval_expanded.json
python run_rag.py --models qwen3:1.7b qwen2.5-coder:1.5b --retrieval results/retrieval_expanded.json --output results/rag_expanded.json
python make_score_sheet.py --run results/rag_expanded.json --labels data/pilot_labels.jsonl data/expanded_labels.jsonl --skip-unlabeled --output results/expanded_score_sheet.csv
```

The score sheet includes only questions with approved labels and leaves judgment fields blank for human review. The nine fixed fixtures establish that the *known migration examples* preserve their declared outputs; model responses must still be checked against those labels. The current curated corpus has evidence for 11 questions, including Q17 and Q22. The remaining questions help measure preflight and evidence-gap behavior but are not ready for migration accuracy scoring.

### Reviewed expanded outcome

The project owner approved the [per-answer judgments](results/expanded_score_sheet_reviewed.csv). The [scored record](results/expanded_scored.json) contains the judgments, summary, routing counts, source-file hashes, and limitations. All 24 questions ran under both models and retrieval configurations without recorded generation errors. Of 96 responses, 44 came from models, 28 from shared preflight, and 24 from evidence-gap handling. Only nine model-backed migration questions (Q02–Q10) contribute to the migration totals below.

| Model | Baseline migration score | Version-aware migration score | Baseline citations supplied | Version-aware citations supplied |
| --- | ---: | ---: | ---: | ---: |
| Qwen3 1.7B | 16/18 | 13/18 | 7/9 | 6/9 |
| Qwen2.5 Coder 1.5B | 11/18 | 10/18 | 0/9 | 0/9 |

All supplied citations in these nine cases were judged to point to supporting official sources; citation coverage is reported separately from correctness among citations supplied. All four model/configuration combinations correctly left Q17 unchanged. Q18, Q21, and Q24 passed the approved action labels through shared deterministic preflight and are excluded from model totals. Q22 produced model answers but has no approved gold label, so it is not scored.

A diagnostic check found the selected target passage in the top two retrieval results for 10/11 evidence-covered questions with baseline retrieval and 11/11 with version-aware retrieval. Despite that retrieval improvement, version-aware generation scored lower in this run. Common errors included `ignore_index=True` discarding indices, `df.items` used without a call, and incorrect dtype or datetime examples. These results are limited to a small curated corpus and nine scored migrations; they do not establish a general ranking of the systems.

## Project status

The 24-question dataset, a non-executing prototype, nine cross-version behavioral fixtures, an open-model comparison harness, a reviewed six-question pilot, and a reviewed expanded run are present. Thirteen gold labels are approved. A broader documentation index and additional manually labeled cases remain planned. See [IMPLEMENTATION.md](IMPLEMENTATION.md) for the build order and evaluation details.
