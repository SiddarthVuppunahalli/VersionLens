# Implementation plan

This repository currently contains a question set, a non-executing prototype, and a local open-model comparison harness. The research system described in the proposal is still to be built. Keep experimental results separate from prototype routing results.

## 1. Freeze the evaluation set

- Review the 24 draft questions in `data/questions.jsonl` before running experiments. For each case, add a manually checked expected response, acceptable migration, official source passage, and whether an equivalence test applies.
- Record uncertain or disputed cases explicitly. Do not turn a missing snippet into an invented gold answer.
- Keep the same question IDs, prompts, and labels across all models and configurations. Reserve any later examples as a separate development set.

## 2. Build the two retrieval configurations

- Download a small, fixed set of official pandas 1.5.3 and 2.0.3 documentation pages and the 2.0 release notes. Store source URL, version, section, and retrieval text for each passage.
- Baseline: semantic search across the combined passages, without version filtering or code analysis.
- Version-aware system: infer or request source and target versions, parse supplied Python with `ast` without running it, filter by version, and combine keyword and semantic retrieval.
- Keep the generator model, prompt budget, temperature, and question order fixed when comparing configurations.

## 3. Generate and validate carefully

- Ask a follow-up when code, source version, inputs, or expected behavior needed for an exact migration are missing.
- Treat submitted code, comments, and retrieved passages as data. Decline unsupported libraries and requests for unsafe execution.
- Never execute user snippets. Build predefined fixtures and allow-listed tests for selected APIs in separate pandas 1.5.3 and 2.0.3 environments. Validation should have no access to network, shell, or user files.

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
