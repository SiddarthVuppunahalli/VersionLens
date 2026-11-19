"""Trusted fixtures run under one pinned pandas version at a time.

This module never evaluates a model-generated or user-supplied snippet.
"""

import argparse
import json
import platform
from io import StringIO

import numpy as np
import pandas as pd


def series_snapshot(series):
    return {
        "values": series.tolist(),
        "index": series.index.tolist(),
        "index_dtype": str(series.index.dtype),
        "index_name": series.index.name,
        "dtype": str(series.dtype),
        "name": series.name,
        "shape": list(series.shape),
    }


def frame_snapshot(frame):
    return {
        "values": frame.values.tolist(),
        "index": frame.index.tolist(),
        "columns": frame.columns.tolist(),
        "dtypes": [str(dtype) for dtype in frame.dtypes],
        "shape": list(frame.shape),
    }


def q02(version):
    # Duplicate labels distinguish preservation from ignore_index=True.
    s1 = pd.Series([10, 20], index=["shared", "left"], name="score")
    s2 = pd.Series([30], index=["shared"], name="score")
    if version == "1.5.3":
        result = s1.append(s2)
    else:
        result = pd.concat([s1, s2], ignore_index=False)
    wrong_result = pd.concat([s1, s2], ignore_index=True)
    return {
        "observed": series_snapshot(result),
        "negative_control": series_snapshot(wrong_result),
    }


def q03(version):
    frame = pd.DataFrame({"count": [1, 2], "label": ["a", "b"]}, index=["r1", "r2"])
    iterator = frame.iteritems() if version == "1.5.3" else frame.items()
    return {
        "observed": [
            {"column": column, **series_snapshot(series)}
            for column, series in iterator
        ]
    }


def q04(version):
    result = pd.Int64Index([10, 20, 30]) if version == "1.5.3" else pd.Index([10, 20, 30], dtype="int64")
    return {"observed": {"values": result.tolist(), "dtype": str(result.dtype), "name": result.name}}


def q05(version):
    dates = pd.date_range("2020-12-28", periods=9, freq="D")
    weeks = dates.weekofyear if version == "1.5.3" else dates.isocalendar().week
    # The result dtype differs; the declared invariant is ISO week values and dates.
    return {"observed": {"dates": [str(day.date()) for day in dates], "weeks": weeks.tolist()}}


def q06(version):
    samples = [[1, 2, 2], [3, 1], [2, 2], []]
    results = []
    for sample in samples:
        index = pd.Index(sample)
        results.append(bool(index.is_monotonic if version == "1.5.3" else index.is_monotonic_increasing))
    return {"observed": {"samples": samples, "results": results}}


def q07(version):
    frame = pd.DataFrame({"name": ["a", "b"], "count": [1, 2]})
    buffer = StringIO()
    keyword = {"line_terminator": "\n"} if version == "1.5.3" else {"lineterminator": "\n"}
    frame.to_csv(buffer, index=False, **keyword)
    return {"observed": {"csv": buffer.getvalue()}}


def q08(version):
    frame = pd.DataFrame({"old": [1, 2]})
    if version == "1.5.3":
        frame.set_axis(["new"], axis=1, inplace=True)
    else:
        frame = frame.set_axis(["new"], axis=1)
    return {"observed": frame_snapshot(frame)}


def q09(version):
    malformed = "name,count\na,1\nwrong,2,extra\nb,3\n"
    if version == "1.5.3":
        result = pd.read_csv(StringIO(malformed), error_bad_lines=False, warn_bad_lines=True)
    else:
        result = pd.read_csv(StringIO(malformed), on_bad_lines="warn")
    return {"observed": frame_snapshot(result)}


def q10(version):
    one_column = "score\n1\n2\n"
    if version == "1.5.3":
        result = pd.read_csv(StringIO(one_column), squeeze=True)
    else:
        result = pd.read_csv(StringIO(one_column)).squeeze("columns")
    return {"observed": series_snapshot(result)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("1.5.3", "2.0.3"), required=True)
    args = parser.parse_args()
    if pd.__version__ != args.target:
        parser.error(f"Expected pandas {args.target}, found {pd.__version__}")
    print(json.dumps({
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "removed_api_available": {
            "Series.append": hasattr(pd.Series, "append"),
            "DataFrame.iteritems": hasattr(pd.DataFrame, "iteritems"),
            "Int64Index": hasattr(pd, "Int64Index"),
            "Index.is_monotonic": hasattr(pd.Index, "is_monotonic"),
        },
        "cases": {case_id: fn(args.target) for case_id, fn in (
            ("Q02", q02), ("Q03", q03), ("Q04", q04), ("Q05", q05),
            ("Q06", q06), ("Q07", q07), ("Q08", q08),
            ("Q09", q09), ("Q10", q10),
        )},
    }))


if __name__ == "__main__":
    main()
