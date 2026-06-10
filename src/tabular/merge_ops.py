import pandas as pd


def merge_frames_by_index(
    left: pd.DataFrame,
    right: pd.DataFrame,
    index: pd.Index,
    skip_existing_columns: bool = True,
) -> pd.DataFrame:
    """Horizontally merges two frames and aligns output to the provided index."""
    left_df = left if left is not None else pd.DataFrame(index=index)
    right_df = right if right is not None else pd.DataFrame(index=index)

    if left_df.empty:
        left_df = pd.DataFrame(index=index)
    if right_df.empty:
        right_df = pd.DataFrame(index=index)

    if skip_existing_columns:
        cols = [c for c in right_df.columns if c not in left_df.columns]
        right_df = right_df[cols]

    merged = pd.concat([left_df, right_df], axis=1)
    return merged.loc[index]
