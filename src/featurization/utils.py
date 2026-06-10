import os
import pandas as pd
from typing import List
from featurization.core.path_coordinator import PathCoordinator

def load_kmds_metadata(metadata_path: str) -> pd.DataFrame:
    """Reads a KMDS metadata CSV, handling signatures and header normalization."""
    if not os.path.exists(metadata_path):
        return pd.DataFrame()
    
    skip = 0
    with open(metadata_path, 'r', encoding='utf-8-sig') as f:
        for i, line in enumerate(f):
            if "provisional_entity_assignment" in line.lower() or "attribute_name" in line.lower():
                skip = i
                break
            if i > 5: # Safety break
                break

    df = pd.read_csv(metadata_path, skiprows=skip, comment="#", encoding='utf-8-sig')
    
    # Aggressive header normalization to strip quotes, casing, and whitespace
    df.columns = [
        str(c).lower().strip().replace('"', '').replace("'", "") 
        for c in df.columns
    ]
    return df

def get_entity_list(resolver: PathCoordinator) -> List[str]:
    """
    Locates the metadata table via the PathCoordinator, identifies the unique entity column,
    and returns a unique list of defined entities (e.g., Borrower, Lender, Property).
    """
    metadata_path = resolver.metadata_path
    df = load_kmds_metadata(metadata_path)
    
    if df.empty:
        print(f"❌ Error: get_entity_list could not find or load file at: {metadata_path}")
        return []

    # Resolve entity column via substring matching to handle potential CSV artifacts
    entity_col = next((c for c in df.columns if "provisional_entity_assignment" in c), None)

    if entity_col and entity_col in df.columns:
        # Extract unique set, drop empty values, and return as a sorted list
        entities = df[entity_col].dropna().unique().tolist()
        return sorted([str(e).strip() for e in entities if str(e).strip()])

    return []