import pandas as pd

from tabular.feature_space import select_model_features
from tabular.modeling_filter import drop_leakage_prone_columns
from tabular.target_encoding import select_categorical_columns


def test_drop_leakage_prone_columns_supports_generic_patterns_and_keep_cols():
    data = pd.DataFrame(
        {
            "label": ["yes", "no", "yes"],
            "label_raw": ["A", "B", "C"],
            "target": [1.0, 0.0, 1.0],
            "industry": ["retail", "food", "retail"],
        }
    )

    filtered = drop_leakage_prone_columns(data=data, patterns=("label",), keep_cols=("target",))

    assert "label" not in filtered.columns
    assert "label_raw" not in filtered.columns
    assert "target" in filtered.columns
    assert "industry" in filtered.columns


def test_select_categorical_columns_excludes_pattern_matched_fields():
    data = pd.DataFrame(
        {
            "status_text": ["paid", "charged_off", "current"],
            "STATUS_DETAIL": ["good", "bad", "good"],
            "industry": ["retail", "food", "retail"],
            "target": [1.0, 0.0, -1.0],
        }
    )

    cat_cols = select_categorical_columns(data=data, exclude_name_patterns=("status",))

    assert "industry" in cat_cols
    assert "status_text" not in cat_cols
    assert "STATUS_DETAIL" not in cat_cols


def test_select_model_features_excludes_pattern_matched_candidates():
    train_df = pd.DataFrame(
        {
            "status": ["paid", "charged_off", "paid", "charged_off"],
            "status_reason": ["on_time", "late", "on_time", "late"],
            "industry_te": [0.8, 0.2, 0.7, 0.3],
            "gross_revenue": [100.0, 200.0, 120.0, 180.0],
            "target": [1.0, 0.0, 1.0, 0.0],
        }
    )

    selected = select_model_features(
        train_df=train_df,
        candidate_cols=["status", "status_reason", "industry_te", "gross_revenue", "target"],
        target_col="target",
        method="threshold",
        min_non_null_rate=0.0,
        min_unique=2,
        exclude_candidate_name_patterns=("status",),
    )

    assert "industry_te" in selected
    assert "gross_revenue" in selected
    assert "status" not in selected
    assert "status_reason" not in selected
    assert "target" not in selected
