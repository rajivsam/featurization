import pandas as pd

def get_categorical_subset(context: dict, drop_filter: list = None) -> pd.DataFrame:
    """
    Package Component: Identifies categorical variables based on KMDS metadata
    and validates them against Pandas dtypes.
    """
    loader = context.get("loader")
    data = context.get("data")
    metadata = getattr(loader, "metadata", None) if loader is not None else context.get("metadata")

    if data is None or data.empty or metadata is None or metadata.empty:
        return pd.DataFrame()

    # 1. Identify candidates using OR logic:
    #    - logical_type == categorical in metadata, OR
    #    - pandas categorical-compatible dtypes in data.
    pandas_cats_norm = {
        str(c).lower().strip()
        for c in data.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    }

    logical_cats_norm = set()
    if "logical_type" in metadata.columns and "attribute_name" in metadata.columns:
        logical_cats_norm = {
            str(attr).lower().strip()
            for attr in metadata.loc[
                metadata["logical_type"].astype(str).str.lower().str.strip() == "categorical",
                "attribute_name",
            ].tolist()
        }

    cat_candidates_norm = pandas_cats_norm.union(logical_cats_norm)

    # 2. Apply the drop filter
    if drop_filter:
        drop_filter_norm = {str(c).lower().strip() for c in drop_filter}
        cat_candidates_norm = {c for c in cat_candidates_norm if c not in drop_filter_norm}

    # 3. Preserve original data column order in the returned subset.
    final_columns = [
        col for col in data.columns
        if str(col).lower().strip() in cat_candidates_norm
    ]

    return data[final_columns]