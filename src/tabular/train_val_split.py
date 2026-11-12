import pandas as pd
from sklearn.model_selection import train_test_split

from featurization.core.task_registry import get_task_defaults, normalize_task_type


def assign_train_val_split(
    data: pd.DataFrame,
    target_col: str,
    val_size: float = 0.2,
    random_state: int = 42,
    split_col: str = "dataset_partition",
    legacy_split_col: str = "dataset_split",
    test_size: float = 0.0,
    task_type: str = "classification",
    time_col: str | None = None,
) -> pd.DataFrame:
    """Adds canonical train/validation/test labels with task-aware splitting behavior."""
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

    task_family = normalize_task_type(task_type)
    default_cfg = get_task_defaults(task_family)
    split_strategy = str(default_cfg.get("split_strategy", "stratified")).strip().lower()

    idx = data.index
    y = data[target_col]
    out = pd.DataFrame(index=idx)
    out[split_col] = "train"
    out[legacy_split_col] = "train"

    if task_family == "clustering":
        return out

    if task_family == "time_to_event":
        if time_col is None:
            time_col = target_col if target_col in data.columns else None
        if time_col is not None and time_col in data.columns:
            ordered = data.sort_values(time_col, kind="mergesort").index
            validation_n = max(1, int(round(len(ordered) * val_size)))
            val_idx = ordered[-validation_n:]
            out.loc[val_idx, split_col] = "validation"
            out.loc[val_idx, legacy_split_col] = "val"
            return out

    if split_strategy == "random":
        train_idx, val_idx = train_test_split(
            idx,
            test_size=val_size,
            random_state=int(random_state),
        )
        out.loc[val_idx, split_col] = "validation"
        out.loc[val_idx, legacy_split_col] = "val"
        return out

    if split_strategy == "none":
        return out

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
