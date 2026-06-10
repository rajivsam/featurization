import pandas as pd


def filter_binary_universe(
    data: pd.DataFrame,
    target_col: str = "loan_status_r",
    drop_class: float = -1.0,
) -> pd.DataFrame:
    """Filters out a designated class (e.g. active=-1) from the modeling universe."""
    if data is None or data.empty:
        return pd.DataFrame()
    if target_col not in data.columns:
        raise KeyError(f"Required target column '{target_col}' not found.")

    return data.loc[data[target_col] != drop_class].copy()


def validate_binary_target(
    data: pd.DataFrame,
    target_col: str = "loan_status_r",
    allowed: tuple = (0.0, 1.0),
) -> None:
    """Validates that the target universe is strictly binary."""
    if data is None or data.empty:
        return
    if target_col not in data.columns:
        raise KeyError(f"Required target column '{target_col}' not found.")

    present = set(data[target_col].dropna().astype(float).unique().tolist())
    allowed_set = set(float(v) for v in allowed)
    unexpected = sorted(present - allowed_set)
    if unexpected:
        raise ValueError(
            f"Binary target validation failed for '{target_col}'. Unexpected labels: {unexpected}"
        )
