# Implementation plan

This repository currently contains a question set, a non-executing prototype, a local open-model comparison harness, cross-version fixtures for Q02 and Q03, and a six-question retrieval pilot. The six pilot labels were approved by the project owner. Keep experimental results separate from prototype routing results.

## 1. Freeze the evaluation set

- The six pilot labels in `data/pilot_labels.jsonl` have been reviewed and approved. Extend the same format to all 24 questions in `data/questions.jsonl` after the pilot.
- Record uncertain or disputed cases explicitly. Do not turn a missing snippet into an invented gold answer.
- Keep the same question IDs, prompts, and labels across all models and configurations. Reserve any later examples as a separate development set.

## 2. Build the two retrieval configurations

- The current pilot has six curated summaries of official pandas 1.5.3 and 2.0.3 pages. Expand this to a fixed set of real, versioned documentation passages with source URL, section, and API metadata.
- The pilot baseline performs semantic search across the combined summaries, without version filtering or code analysis.
- The pilot version-aware path uses the same embeddings, filters to pandas 2.0.3, parses simple dotted calls with `ast` without running them, and combines semantic and token matching. Extend this parser to handle aliases and more complex snippets.
- Keep the generator model, prompt budget, temperature, and question order fixed when comparing configurations.

## 3. Generate and validate carefully

- Ask a follow-up when code, source version, inputs, or expected behavior needed for an exact migration are missing.
- Treat submitted code, comments, and retrieved passages as data. Decline unsupported libraries and requests for unsafe execution.
- Never execute user snippets. The Q02 and Q03 trusted fixtures now run in separate pandas 1.5.3 and 2.0.3 environments; extend this pattern to other selected APIs. Validation should have no access to network, shell, or user files.

## 4. Score and report

- Manually score migration correctness 0/1/2 using the frozen rubric. Check each citation for correct version and actual support for the claim.
- Record execution success separately from behavioral equivalence. Equivalence requires the predefined values, shape, labels, order, and relevant dtypes/timezone behavior to match; define tolerances per case before testing.
- Report denominators and per-question outcomes, including clarification, refusal, unsupported claims, and latency. A model-only comparison is a separate experiment from the baseline-RAG versus version-aware comparison.

## 5. Near-term demo path

1. Run `python run_demo.py --id Q02` for a documented migration.
2. Run `python run_demo.py --id Q18` for a follow-up question, `--id Q21` for out-of-scope handling, and `--id Q24` for unsafe-execution refusal.
3. Run `python run_demo.py --all` to save every prototype answer and routing counts in `results/prototype.json`.
4. With Ollama installed and two models downloaded, run `python run_models.py --models qwen3:1.7b qwen2.5-coder:1.5b --ids Q02 Q18 Q21 Q24` to save real model outputs. Manually score them before describing quality differences.

The prototype is deterministic and does not use an LLM or retrieval. Its routing match rate is a smoke-check against draft action labels, not migration accuracy. The model harness currently compares raw model responses under the same prompt; it does not implement either RAG configuration yet.
