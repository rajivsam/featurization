import pandas as pd
import pytest

from tabular.feature_space import infer_top_k_from_importances


def test_infer_top_k_fixed_mode_honors_cap():
    importances = pd.Series([0.4, 0.3, 0.2, 0.1], index=["a", "b", "c", "d"])

    k = infer_top_k_from_importances(
        importances=importances,
        mode="fixed",
        fixed_top_k=2,
        min_k=1,
        max_k=0,
    )

    assert k == 2


def test_infer_top_k_kneedle_mode_returns_bounded_value():
    importances = pd.Series(
        [0.31, 0.29, 0.27, 0.12, 0.11, 0.10, 0.09],
        index=["f1", "f2", "f3", "f4", "f5", "f6", "f7"],
    )

    k = infer_top_k_from_importances(
        importances=importances,
        mode="kneedle",
        fixed_top_k=50,
        min_k=2,
        max_k=5,
        kneedle_sensitivity=1.0,
        kneedle_curve="convex",
        kneedle_direction="decreasing",
    )

    assert 2 <= k <= 5


def test_infer_top_k_respects_min_ratio_floor():
    importances = pd.Series([0.5, 0.3, 0.2, 0.1], index=["a", "b", "c", "d"])

    k = infer_top_k_from_importances(
        importances=importances,
        mode="fixed",
        fixed_top_k=1,
        min_k=1,
        min_ratio=0.5,
        max_k=0,
    )

    assert k == 2


def test_infer_top_k_raises_when_kneed_required_but_missing(monkeypatch):
    import importlib

    real_import_module = importlib.import_module

    def fake_import_module(name: str):
        if name == "kneed":
            raise ImportError("kneed missing")
        return real_import_module(name)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    importances = pd.Series([0.4, 0.2, 0.1], index=["a", "b", "c"])
    with pytest.raises(RuntimeError):
        infer_top_k_from_importances(
            importances=importances,
            mode="kneedle",
            fixed_top_k=3,
            require_kneedle=True,
        )


def test_infer_top_k_target_feature_count_overrides_knee():
    importances = pd.Series(
        [0.4, 0.39, 0.38, 0.37, 0.36, 0.35, 0.34, 0.33, 0.32, 0.31, 0.30, 0.29],
        index=[f"f{i}" for i in range(1, 13)],
    )

    k = infer_top_k_from_importances(
        importances=importances,
        mode="kneedle",
        fixed_top_k=50,
        min_k=1,
        min_ratio=0.5,
        min_feature_count=10,
        target_feature_count=10,
        max_k=50,
        require_kneedle=True,
    )

    assert k == 10
