import re
import pandas as pd
from typing import List, Optional

def exclusion_filter(
    df: pd.DataFrame, 
    explicit_list: Optional[List[str]] = None, 
    regex_pattern: Optional[str] = None
) -> pd.DataFrame:
    """Removes columns from a DataFrame based on a string list or a regular expression pattern."""
    columns_to_drop = set()

    # 1. Process explicit exact match list
    if explicit_list:
        for col in explicit_list:
            if col in df.columns:
                columns_to_drop.add(col)

    # 2. Process regular expression rule matching
    if regex_pattern:
        compiled_regex = re.compile(regex_pattern)
        for col in df.columns:
            if compiled_regex.search(col):
                columns_to_drop.add(col)

    # Apply drop sequence safely
    if columns_to_drop:
        print(f"   Dropped {len(columns_to_drop)} columns: {list(columns_to_drop)}")
        return df.drop(columns=list(columns_to_drop))
        
    return df
