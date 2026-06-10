import pandas as pd


def select_model_features(
    train_df: pd.DataFrame,
    candidate_cols: list[str],
    min_non_null_rate: float = 0.01,
    min_unique: int = 2,
) -> list[str]:
    """Selects model features from train data using simple stability thresholds."""
    if train_df is None or train_df.empty:
        return []

    selected: list[str] = []
    n_rows = len(train_df)
    for col in candidate_cols:
        if col not in train_df.columns:
            continue

        non_null_rate = float(train_df[col].notna().sum()) / float(n_rows)
        n_unique = int(train_df[col].nunique(dropna=True))

        if non_null_rate >= float(min_non_null_rate) and n_unique >= int(min_unique):
            selected.append(col)

    return selected


def project_feature_space(
    data: pd.DataFrame,
    feature_cols: list[str],
    fill_value: float = 0.0,
) -> pd.DataFrame:
    """Projects data into an exact feature schema, filling missing columns."""
    if data is None or data.empty:
        return pd.DataFrame(columns=feature_cols)

    projected = data.reindex(columns=feature_cols)
    return projected.fillna(fill_value)
