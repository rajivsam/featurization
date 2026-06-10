import pandas as pd


def drop_leakage_prone_columns(
    data: pd.DataFrame,
    patterns: tuple[str, ...] | list[str] | None = None,
    keep_cols: tuple[str, ...] | list[str] | None = None,
) -> pd.DataFrame:
    """Drops columns whose names match any case-insensitive pattern."""
    if data is None or data.empty:
        return pd.DataFrame()

    normalized_patterns = tuple(str(p).lower() for p in (patterns or []) if p)
    if not normalized_patterns:
        return data.copy()

    keep = set(keep_cols or [])
    cols_to_drop: list[str] = []

    for col in data.columns:
        col_lower = str(col).lower()
        if col in keep:
            continue
        if any(pattern in col_lower for pattern in normalized_patterns):
            cols_to_drop.append(col)

    if not cols_to_drop:
        return data.copy()

    return data.drop(columns=cols_to_drop).copy()


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
