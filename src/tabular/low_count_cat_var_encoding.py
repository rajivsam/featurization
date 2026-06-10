import pandas as pd

def get_categorical_subset(context: dict, drop_filter: list = None) -> pd.DataFrame:
    """
    Package Component: Identifies categorical variables based on KMDS metadata
    and validates them against Pandas dtypes.
    """
    loader = context.get("loader")
    data = context.get("data")
    metadata = loader.metadata

    if data is None or data.empty or metadata is None or metadata.empty:
        return pd.DataFrame()

    # 1. Identify categorical candidates from metadata
    # We look for attributes that are NOT flagged as numeric or geographic 
    # and intersect them with pandas 'object' or 'category' types.
    pandas_cats = data.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Metadata attribute names (normalized)
    meta_attrs = [str(a).strip() for a in metadata['attribute_name'].unique()]
    
    # Intersection: Categorical according to both metadata and dtypes
    cat_candidates = [c for c in pandas_cats if c in meta_attrs]

    # 2. Apply the drop filter
    if drop_filter:
        cat_candidates = [c for c in cat_candidates if c not in drop_filter]

    # 3. Robust column matching for the final subset
    data_cols_lower = {str(c).lower().strip(): c for c in data.columns}
    final_columns = []
    for attr in cat_candidates:
        clean_attr = str(attr).lower().strip()
        if clean_attr in data_cols_lower:
            final_columns.append(data_cols_lower[clean_attr])

    return data[final_columns]