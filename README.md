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

## Project status

The scope, comparison design, draft benchmark, evaluation rubric, and safety constraints are defined. Implementation and experiments are the next phase.
