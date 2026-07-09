import os
import pandas as pd
from typing import Any, Dict, List
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

    entity_col = next((c for c in df.columns if "provisional_entity_assignment" in c), None)
    if entity_col is None:
        return []

    entities = df[entity_col].dropna().astype(str).str.strip()
    return sorted([e for e in entities.unique() if e])


def get_package_info() -> Dict[str, Any]:
    """Return package discovery metadata for clients."""
    from featurization import __version__ as package_version
    from featurization.cli import get_cli_command_names

    return {
        "package_name": "kmds-featurization",
        "version": package_version,
        "entry_point": "featurization-cli",
        "cli_commands": get_cli_command_names(),
        "documentation_note": (
            "This package no longer ships internal docs in the installed package. "
            "Use the repository top-level documents/ folder for onboarding and implementation guidance."
        ),
        "usage": {
            "overview": (
                "Use this package by configuring a workspace in featurizer_config.yaml, "
                "then running the CLI from that workspace. For cross-sectional workflows, "
                "follow the cross-sectional guide; for event-log survival workflows, "
                "follow the survival guide."
            ),
            "cross_sectional_guide": "documents/user_guide_cs_featurization.md",
            "survival_guide": "documents/survival_featurization_pipeline.md",
            "guidance": (
                "Feature selection is recommended for wide and short datasets. "
                "This package does not provide a dedicated featurization pipeline for wide and short datasets."
            ),
        },
    }