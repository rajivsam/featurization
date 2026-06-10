import pandas as pd
from sklearn.model_selection import train_test_split


def assign_train_val_split(
    data: pd.DataFrame,
    target_col: str,
    val_size: float = 0.2,
    random_state: int = 42,
    split_col: str = "dataset_split",
) -> pd.DataFrame:
    """Adds a deterministic train/val split flag with stratification on target."""
    if data is None or data.empty:
        return pd.DataFrame()
    if target_col not in data.columns:
        raise KeyError(f"Required target column '{target_col}' not found.")

    if not 0.0 < float(val_size) < 1.0:
        raise ValueError(f"val_size must be in (0, 1). Received: {val_size}")

    idx = data.index
    y = data[target_col]

    train_idx, val_idx = train_test_split(
        idx,
        test_size=float(val_size),
        random_state=int(random_state),
        stratify=y,
    )

    out = pd.DataFrame(index=idx)
    out[split_col] = "train"
    out.loc[val_idx, split_col] = "val"
    out.loc[train_idx, split_col] = "train"
    return out
