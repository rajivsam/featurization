import pandas as pd

from tabular.merge_ops import merge_frames_by_index


def test_merge_frames_by_index_aligns_to_index_order():
    idx = pd.Index([3, 1, 2], name="record_id")
    left = pd.DataFrame({"cat": ["a", "b", "c"]}, index=[1, 2, 3])
    right = pd.DataFrame({"num": [10, 20, 30]}, index=[1, 2, 3])

    merged = merge_frames_by_index(left=left, right=right, index=idx)

    assert merged.index.tolist() == [3, 1, 2]
    assert merged.columns.tolist() == ["cat", "num"]


def test_merge_frames_by_index_skips_existing_columns():
    idx = pd.Index([1, 2], name="record_id")
    left = pd.DataFrame({"x": [100, 200]}, index=idx)
    right = pd.DataFrame({"x": [1, 2], "y": [3, 4]}, index=idx)

    merged = merge_frames_by_index(left=left, right=right, index=idx, skip_existing_columns=True)

    assert merged.columns.tolist() == ["x", "y"]
    assert merged["x"].tolist() == [100, 200]
    assert merged["y"].tolist() == [3, 4]


def test_merge_frames_by_index_handles_missing_inputs():
    idx = pd.Index([1, 2], name="record_id")
    right = pd.DataFrame({"y": [3, 4]}, index=idx)

    merged = merge_frames_by_index(left=None, right=right, index=idx)

    assert merged.columns.tolist() == ["y"]
    assert merged["y"].tolist() == [3, 4]
