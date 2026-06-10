import pandas as pd


def select_categorical_columns(data: pd.DataFrame, exclude_cols: list[str] | None = None) -> list[str]:
    """Selects categorical columns using pandas dtypes and excludes explicit columns."""
    if data is None or data.empty:
        return []

    exclude = set(exclude_cols or [])
    cat_cols = data.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    return [c for c in cat_cols if c not in exclude]


def fit_target_encoder(train_df: pd.DataFrame, y_col: str, cat_cols: list[str]):
    """Fits category_encoders.TargetEncoder on train partition only."""
    if train_df is None or train_df.empty:
        raise ValueError("train_df is empty. Cannot fit target encoder.")
    if y_col not in train_df.columns:
        raise KeyError(f"Required target column '{y_col}' not found in train data.")

    from category_encoders import TargetEncoder

    encoder = TargetEncoder(cols=cat_cols, handle_missing="value", handle_unknown="value")
    encoder.fit(train_df[cat_cols], train_df[y_col])
    return encoder


def transform_with_encoder(
    df: pd.DataFrame,
    encoder,
    cat_cols: list[str],
    suffix: str = "_te",
) -> pd.DataFrame:
    """Transforms categorical columns with a fitted target encoder and suffixes outputs."""
    if df is None or df.empty:
        return pd.DataFrame()

    transformed = encoder.transform(df[cat_cols])
    transformed = transformed.copy()
    transformed.columns = [f"{c}{suffix}" for c in transformed.columns]
    transformed.index = df.index
    return transformed
