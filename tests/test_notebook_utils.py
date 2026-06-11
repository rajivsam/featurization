import os
import pandas as pd
import pytest
import yaml

from featurization.core.path_coordinator import PathCoordinator
from featurization.notebook_utils import (
    build_notebook_resolver,
    get_featurization_artifact_paths,
    get_featurization_artifact_status,
    load_featurized_dataset,
    load_model_ready_dataset,
)


def test_notebook_utils_returns_expected_paths(tmp_path):
    working_dir = str(tmp_path)
    config = {
        "featurization_output_dir": "featurization",
    }
    resolver = PathCoordinator(working_dir=working_dir, config=config)

    artifact_paths = get_featurization_artifact_paths(resolver)

    assert artifact_paths["featurized_dataset_path"].endswith(
        os.path.join("data", "featurization", "featurized_data.csv")
    )
    assert artifact_paths["model_ready_dataset_path"].endswith(
        os.path.join("data", "featurization", "model_ready_numeric_data.csv")
    )
    assert artifact_paths["feature_selection_knee_curve_path"].endswith(
        os.path.join("data", "featurization", "feature_selection_knee_curve.png")
    )


def test_notebook_utils_reports_existing_file_status(tmp_path):
    working_dir = str(tmp_path)
    config = {
        "featurization_output_dir": "featurization",
    }
    resolver = PathCoordinator(working_dir=working_dir, config=config)

    output_dir = os.path.join(working_dir, "data", "featurization")
    os.makedirs(output_dir, exist_ok=True)

    featurized_path = resolver.featurized_dataset_path
    model_ready_path = resolver.model_ready_dataset_path
    knee_curve_path = resolver.feature_selection_knee_curve_path

    pd.DataFrame({"a": [1, 2]}).to_csv(featurized_path, index=False)
    pd.DataFrame({"b": [3, 4]}).to_csv(model_ready_path, index=False)
    with open(knee_curve_path, "w", encoding="utf-8") as fh:
        fh.write("PNG PLACEHOLDER")

    status = get_featurization_artifact_status(resolver)

    assert status["featurized_dataset_path"]["exists"] is True
    assert status["model_ready_dataset_path"]["exists"] is True
    assert status["feature_selection_knee_curve_path"]["exists"] is True


def test_notebook_utils_can_load_output_csvs(tmp_path):
    working_dir = str(tmp_path)
    config = {
        "featurization_output_dir": "featurization",
    }
    resolver = PathCoordinator(working_dir=working_dir, config=config)

    output_dir = os.path.join(working_dir, "data", "featurization")
    os.makedirs(output_dir, exist_ok=True)

    pd.DataFrame({"record_id": [1, 2], "value": [10, 20]}).to_csv(
        resolver.featurized_dataset_path, index=False
    )
    pd.DataFrame({"record_id": [1, 2], "score": [0.1, 0.9]}).to_csv(
        resolver.model_ready_dataset_path, index=False
    )

    loaded_featurized = load_featurized_dataset(resolver)
    loaded_model_ready = load_model_ready_dataset(resolver)

    assert list(loaded_featurized.columns) == ["record_id", "value"]
    assert list(loaded_model_ready.columns) == ["record_id", "score"]
    assert len(loaded_featurized) == 2
    assert len(loaded_model_ready) == 2


def test_notebook_utils_builds_resolver_from_notebook_dir(tmp_path):
    workspace_root = tmp_path
    notebook_dir = tmp_path / "notebooks"
    notebook_dir.mkdir()

    config = {
        "featurization_output_dir": "featurization",
    }
    config_path = workspace_root / "featurizer_config.yaml"
    with open(config_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(config, fh)

    resolver = build_notebook_resolver(str(notebook_dir))
    artifact_paths = get_featurization_artifact_paths(resolver)

    assert artifact_paths["featurized_dataset_path"].endswith(
        os.path.join("data", "featurization", "featurized_data.csv")
    )


def test_notebook_utils_rejects_invalid_notebook_workspace(tmp_path):
    notebook_dir = tmp_path / "notebooks"
    notebook_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="does not appear to be a kmds-featurization workspace"):
        build_notebook_resolver(str(notebook_dir))


def test_notebook_utils_resolves_workspace_artifacts():
    working_dir = "/home/rajiv/programming/dd_parser_cleaner_migration/sba_migration"
    config = {
        "featurization_output_dir": "featurization",
    }
    resolver = PathCoordinator(working_dir=working_dir, config=config)

    artifact_paths = get_featurization_artifact_paths(resolver)

    assert artifact_paths["featurized_dataset_path"].endswith(
        os.path.join("data", "featurization", "featurized_data.csv")
    )
    assert artifact_paths["model_ready_dataset_path"].endswith(
        os.path.join("data", "featurization", "model_ready_numeric_data.csv")
    )
    assert artifact_paths["feature_selection_knee_curve_path"].endswith(
        os.path.join("data", "featurization", "feature_selection_knee_curve.png")
    )
