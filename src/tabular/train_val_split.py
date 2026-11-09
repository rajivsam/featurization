import pandas as pd
from sklearn.model_selection import train_test_split


def assign_train_val_split(
    data: pd.DataFrame,
    target_col: str,
    val_size: float = 0.2,
    random_state: int = 42,
    split_col: str = "dataset_partition",
    legacy_split_col: str = "dataset_split",
    test_size: float = 0.0,
) -> pd.DataFrame:
    """Adds canonical train/validation/test labels with backward-compatible dataset_split output."""
    if data is None or data.empty:
        return pd.DataFrame()
    if target_col not in data.columns:
        raise KeyError(f"Required target column '{target_col}' not found.")

    val_size = float(val_size)
    test_size = float(test_size)
    if not 0.0 < val_size < 1.0:
        raise ValueError(f"val_size must be in (0, 1). Received: {val_size}")
    if not 0.0 <= test_size < 1.0:
        raise ValueError(f"test_size must be in [0, 1). Received: {test_size}")
    if val_size + test_size >= 1.0:
        raise ValueError("val_size + test_size must be less than 1.0.")

    idx = data.index
    y = data[target_col]
    out = pd.DataFrame(index=idx)
    out[split_col] = "train"
    out[legacy_split_col] = "train"

    if test_size > 0:
        train_valid_idx, test_idx = train_test_split(
            idx,
            test_size=test_size,
            random_state=int(random_state),
            stratify=y,
        )
        remaining_y = y.loc[train_valid_idx]
        train_idx, val_idx = train_test_split(
            train_valid_idx,
            test_size=val_size / (1.0 - test_size),
            random_state=int(random_state),
            stratify=remaining_y,
        )

        out.loc[test_idx, split_col] = "test"
        out.loc[val_idx, split_col] = "validation"
        out.loc[val_idx, legacy_split_col] = "val"
        return out

    train_idx, val_idx = train_test_split(
        idx,
        test_size=val_size,
        random_state=int(random_state),
        stratify=y,
    )

    out.loc[val_idx, split_col] = "validation"
    out.loc[val_idx, legacy_split_col] = "val"
    return out
