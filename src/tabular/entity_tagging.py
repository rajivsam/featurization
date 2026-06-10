import pandas as pd

def get_stage_subset(context: dict, entity: str, sub_filter: str) -> pd.DataFrame:
    """
    Filters the primary dataset based on KMDS metadata assignments.
    
    Args:
        context: The execution context containing the 'loader' and 'data'.
        entity: The target 'provisional_entity_assignment' value.
        sub_filter: The target 'sub_filter' value.
        
    Returns:
        pd.DataFrame: A subset of columns matching the domain criteria.
    """
    loader = context.get("loader")
    data = context.get("data")

    if loader is None or data is None or data.empty:
        return pd.DataFrame()

    metadata = loader.metadata
    if metadata is None or metadata.empty:
        return pd.DataFrame()

    # Column names are normalized by load_kmds_metadata in utils.py
    entity_col = "provisional_entity_assignment"
    attr_col = "attribute_name"

    # Step 1: Identify and filter by the entity flag column (e.g., is_geographic)
    flag_col = f"is_{entity.lower().strip()}"
    if flag_col not in metadata.columns:
        # Robust fallback for naming variations (e.g., geographical -> geographic)
        alt_flag = flag_col.replace("geographical", "geographic")
        if alt_flag not in metadata.columns:
            # Check the inverse mapping
            alt_flag = flag_col.replace("geographic", "geographical")

        if alt_flag in metadata.columns:
            flag_col = alt_flag

    if flag_col not in metadata.columns:
        return pd.DataFrame()

    # Filter for attributes where the category flag is true
    is_entity_subset = metadata[metadata[flag_col].astype(str).str.lower().str.strip().isin(['true', '1', 'yes', 'y'])].copy()

    # Step 2: Filter the subset where provisional_entity_assignment matches the sub_filter tag
    is_entity_subset['lc_provisional_entity'] = is_entity_subset[entity_col].astype(str).str.lower().str.strip()
    final_meta = is_entity_subset[is_entity_subset['lc_provisional_entity'] == str(sub_filter).lower().strip()]
    
    target_attributes = final_meta[attr_col].unique().tolist()
    
    # Robust matching: Handle casing/whitespace discrepancies between metadata and CSV
    data_cols_lower = {str(c).lower().strip(): c for c in data.columns}
    final_columns = []
    for attr in target_attributes:
        clean_attr = str(attr).lower().strip()
        if clean_attr in data_cols_lower:
            final_columns.append(data_cols_lower[clean_attr])

    return data[final_columns]