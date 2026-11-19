"""Trusted fixtures run under one pinned pandas version at a time.

This module never evaluates a model-generated or user-supplied snippet.
"""

import argparse
import json
import platform

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
        },
        "cases": {"Q02": q02(args.target), "Q03": q03(args.target)},
    }))


if __name__ == "__main__":
    main()
