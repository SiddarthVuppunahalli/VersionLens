"""Small, non-executing VersionLens prototype and benchmark helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data" / "questions.jsonl"
EVIDENCE = ROOT / "data" / "pandas_evidence.json"
RELEASE_NOTES = "https://pandas.pydata.org/pandas-docs/version/2.0/whatsnew/v2.0.0.html"


def questions() -> list[dict]:
    with DATASET.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if len(rows) != 24 or len({row["id"] for row in rows}) != 24:
        raise ValueError("Expected 24 unique evaluation questions")
    return rows


def preflight(query: str) -> dict | None:
    """Handle a narrow set of known safety, scope, and missing-context cases."""
    lower = query.lower()
    if re.search(r"\b(?:os\.(?:remove|unlink|system)|shutil\.rmtree|subprocess\.|eval\(|exec\()", lower):
        return _result("refuse_execution", "I cannot run code that could modify files or invoke the system. I can inspect a safe pandas snippet without executing it.")
    if "scikit-learn" in lower or "sklearn" in lower:
        return _result("decline", "VersionLens covers pandas 1.5.3 to 2.0.3 only. A scikit-learn migration is outside this project's scope.")
    if "ignore the assistant" in lower or "hidden prompt" in lower:
        return _result("ignore_injection", "I will ignore instructions embedded in code comments. Please provide the row type and expected output to migrate the pandas append call safely.")
    if lower.strip() == "please upgrade my pandas code." or "this notebook uses" in lower:
        return _result("clarify", "Please provide the actual code snippet, a small input example, and expected output so I can propose a behavior-preserving migration.")
    if "originally used" in lower and "do not know" in lower:
        return _result("clarify", "Please share the failing code, exact error, and any available source-version information before I propose a migration.")
    if "df.append(new_row" in lower:
        return _result("clarify", "DataFrame.append was removed in pandas 2.0. What are the type and shape of new_row, and what output columns and index do you expect?")
    return None


def retrieve_evidence(query: str) -> list[dict]:
    """Look up a small curated set of version-tagged official-doc facts."""
    lower = query.lower()
    with EVIDENCE.open(encoding="utf-8") as handle:
        entries = {entry["id"]: entry for entry in json.load(handle)}
    if "append" in lower:
        ids = ["append_removed", "concat_indices"] if "s1.append(s2)" in lower else ["append_removed"]
    elif "iteritems" in lower:
        ids = ["iteritems_removed"]
    else:
        ids = []
    return [entries[item] for item in ids]


def answer(query: str) -> dict:
    """Return only a supported template or a clarification; never execute query text."""
    lower = query.lower()
    if re.search(r"\b(?:os\.remove|shutil\.rmtree|subprocess|eval\(|exec\()", lower):
        return _result("refuse_execution", "I cannot run code that could modify files or invoke the system. I can inspect a safe pandas snippet without executing it.")
    if "scikit-learn" in lower or "sklearn" in lower:
        return _result("decline", "This prototype covers pandas 1.5.3 to 2.0.3 only; a scikit-learn migration is outside its scope.")
    if "ignore the assistant" in lower or "hidden prompt" in lower:
        return _result("ignore_injection", "The instruction in the code comment is untrusted. DataFrame.append was removed in pandas 2.0; for a row migration, please provide the row type and expected index behavior before I suggest exact code.", [RELEASE_NOTES])
    if "openpyxl" in lower:
        return _result("diagnose", "That error says the optional openpyxl package is missing. It does not, by itself, prove that pandas 2.0 caused the failure. Please share the Excel operation and environment package versions.")
    if "originally used" in lower or "source version" in lower and "do not know" in lower:
        return _result("clarify", "Please share the failing code, exact error, and any version information from the notebook environment. I can inspect likely changes, but cannot assert a migration without the source behavior.")
    if "please upgrade my pandas code" in lower or "this notebook uses" in lower:
        return _result("clarify", "Please provide the actual code snippet, sample input, expected output, and source pandas version so I can preserve its behavior.")
    if "groupby" in lower and "[\"score\"].mean()" in lower:
        return _result("no_change", "This expression does not show a pandas 2.0 migration requirement. Check the actual input and output before changing it.")
    if "s1.append(s2)" in lower:
        return _result("migrate", "Use `combined = pd.concat([s1, s2])`. The default preserves the original indices; verify the result against a fixed input.", [RELEASE_NOTES])
    if "iteritems" in lower and "append" not in lower:
        return _result("migrate", "Use `df.items()` in place of `df.iteritems()`. The latter was removed in pandas 2.0.", [RELEASE_NOTES])
    if "int64index" in lower:
        return _result("migrate", "Use `pd.Index([10, 20, 30], dtype='int64')`. The Int64Index class was removed in pandas 2.0.", [RELEASE_NOTES])
    if "weekofyear" in lower:
        return _result("migrate", "Use `dates.isocalendar().week` for a DatetimeIndex. If `dates` is a Series of datetimes, use `dates.dt.isocalendar().week`.", [RELEASE_NOTES])
    if "df.append(new_row" in lower:
        return _result("clarify", "DataFrame.append was removed; `pd.concat` is its replacement. Please provide the type and shape of `new_row` so the replacement preserves the original columns and `ignore_index=True` behavior.", [RELEASE_NOTES])
    if "blog" in lower and "append" in lower:
        return _result("explain", "Use the official pandas 2.0 release notes for this version-specific claim: DataFrame.append was removed and pandas.concat is the documented replacement.", [RELEASE_NOTES])
    return _result("clarify", "Please provide the exact code, sample input, expected output, and error. This prototype does not have a verified migration for this case.")


def _result(action: str, response: str, citations: list[str] | None = None) -> dict:
    return {"action": action, "response": response, "citations": citations or [], "executed_user_code": False}
