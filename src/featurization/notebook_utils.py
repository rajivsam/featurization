import os
from typing import Dict

import pandas as pd
import yaml

from featurization.core.path_coordinator import PathCoordinator


def resolve_notebook_workspace_root(notebook_dir: str, config_name: str = "featurizer_config.yaml") -> str:
    """Resolves the KMDS featurization workspace root from a notebook directory."""
    notebook_dir = os.path.abspath(notebook_dir)
    if not os.path.isdir(notebook_dir):
        raise FileNotFoundError(
            f"Notebook directory does not exist: {notebook_dir}"
        )

    workspace_root = os.path.dirname(notebook_dir)
    config_path = os.path.join(workspace_root, config_name)
    if not os.path.isfile(config_path):
        raise FileNotFoundError(
            "This does not appear to be a kmds-featurization workspace. "
            f"Could not find {config_name} in the parent directory of the notebook."
        )

    return workspace_root


def load_workspace_config_from_notebook_dir(notebook_dir: str, config_name: str = "featurizer_config.yaml") -> Dict:
    """Loads the workspace featurizer config from the parent of the notebook directory."""
    workspace_root = resolve_notebook_workspace_root(notebook_dir, config_name=config_name)
    config_path = os.path.join(workspace_root, config_name)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_notebook_resolver(notebook_dir: str, config_name: str = "featurizer_config.yaml") -> PathCoordinator:
    """Builds a PathCoordinator from a notebook directory in a KMDS workspace."""
    workspace_root = resolve_notebook_workspace_root(notebook_dir, config_name=config_name)
    config = load_workspace_config_from_notebook_dir(notebook_dir, config_name=config_name)
    working_dir = config.get("working_dir", workspace_root)
    if working_dir and not os.path.isabs(working_dir):
        working_dir = os.path.abspath(os.path.join(workspace_root, working_dir))
    return PathCoordinator(working_dir=working_dir, config=config)


def _should_show_knee_curve_artifact(resolver: PathCoordinator) -> bool:
    """Returns True when the workspace dataset should expose a knee-curve artifact."""
    return resolver.structural_type == "cross-sectional"


def get_featurization_artifact_paths(resolver: PathCoordinator) -> Dict[str, str]:
    """Returns absolute paths for the main featurization output artifacts."""
    paths = {
        "featurized_dataset_path": resolver.featurized_dataset_path,
        "model_ready_dataset_path": resolver.model_ready_dataset_path,
    }
    paths["feature_selection_knee_curve_path"] = (
        resolver.feature_selection_knee_curve_path
        if _should_show_knee_curve_artifact(resolver)
        else None
    )
    return paths


def get_featurization_artifact_status(resolver: PathCoordinator) -> Dict[str, Dict[str, object]]:
    """Returns path and presence status for featurization artifacts."""
    artifact_paths = get_featurization_artifact_paths(resolver)
    return {
        name: {
            "path": path,
            "exists": os.path.isfile(path) if path else False,
        }
        for name, path in artifact_paths.items()
    }


def get_dd_cleaner_artifact_paths(resolver: PathCoordinator) -> Dict[str, str]:
    """Returns absolute paths for dd-parser-cleaner artifacts in the workspace."""
    return {
        "metadata_path": resolver.metadata_path,
        "featurization_input_path": resolver.featurization_input_path,
    }


def get_featurization_pipeline(resolver: PathCoordinator):
    """Returns the configured featurization pipeline from the workspace config."""
    return resolver.config.get("pipeline", [])


def get_notebook_workspace_artifact_paths(notebook_dir: str, config_name: str = "featurizer_config.yaml") -> Dict[str, str]:
    """Builds a notebook workspace resolver and returns dd-parser-cleaner artifact paths."""
    resolver = build_notebook_resolver(notebook_dir, config_name=config_name)
    return get_dd_cleaner_artifact_paths(resolver)


def load_featurized_dataset(resolver: PathCoordinator, **read_csv_kwargs) -> pd.DataFrame:
    """Loads the consolidated featurized dataset CSV from the featurization output directory."""
    path = resolver.featurized_dataset_path
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Featurized dataset not found at: {path}")
    return pd.read_csv(path, **read_csv_kwargs)


def load_model_ready_dataset(resolver: PathCoordinator, **read_csv_kwargs) -> pd.DataFrame:
    """Loads the model-ready numeric dataset CSV from the featurization output directory."""
    path = resolver.model_ready_dataset_path
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Model-ready dataset not found at: {path}")
    return pd.read_csv(path, **read_csv_kwargs)


def load_data_dictionary_metadata(resolver: PathCoordinator, **read_csv_kwargs) -> pd.DataFrame:
    """Loads dd-parser-cleaner metadata from the configured workspace path."""
    path = resolver.metadata_path
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Data dictionary metadata not found at: {path}")
    return pd.read_csv(path, **read_csv_kwargs)


def load_featurization_input_dataset(resolver: PathCoordinator, **read_csv_kwargs) -> pd.DataFrame:
    """Loads the cleaned input dataset from the configured dd-parser-cleaner output path."""
    path = resolver.featurization_input_path
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Featurization input dataset not found at: {path}")
    return pd.read_csv(path, **read_csv_kwargs)
