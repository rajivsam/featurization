import pandas as pd

from featurization.core.task_registry import get_task_defaults, get_task_runtime_config
from tabular.feature_space import select_model_features
from tabular.train_val_split import assign_train_val_split


def test_regression_runtime_defaults_are_task_aware():
    config = get_task_runtime_config("continuous target")

    assert config["task_type"] == "regression"
    assert config["split_strategy"] == "random"
    assert config["feature_selection"] == "tree_ensemble_regression"


def test_time_to_event_runtime_defaults_are_task_aware():
    config = get_task_defaults("time to event")

    assert config["task_type"] == "time_to_event"
    assert config["split_strategy"] == "time_aware"
    assert config["target_kind"] == "duration_event"


def test_regression_split_and_clustering_selection_are_task_specific():
    regression_df = pd.DataFrame({
        "target": [i for i in range(100)],
        "feature_a": [float(i % 10) for i in range(100)],
        "feature_b": [float((i * 3) % 17) for i in range(100)],
    })
    split_df = assign_train_val_split(
        regression_df,
        target_col="target",
        val_size=0.25,
        task_type="regression",
    )
    validation_share = (split_df["dataset_partition"] == "validation").mean()
    assert abs(validation_share - 0.25) < 0.15

    clustering_df = pd.DataFrame({
        "feature_a": [float(i) for i in range(20)],
        "feature_b": [float(i * 2) for i in range(20)],
        "feature_c": [1.0 for _ in range(20)],
    })
    selected = select_model_features(
        clustering_df,
        candidate_cols=["feature_a", "feature_b", "feature_c"],
        target_col="unused_target",
        method="tree_ensemble",
        task_type="clustering",
        top_k=2,
        top_k_mode="fixed",
        importance_floor=0.0,
    )

    assert "feature_a" in selected
    assert "feature_b" in selected
    assert "feature_c" not in selected
