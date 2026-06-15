import os
import pathlib
import tempfile
import yaml

from featurization.notebook_utils import build_notebook_resolver


def test_build_notebook_resolver_uses_working_dir(tmp_path):
    workspace_root = tmp_path / "workspace"
    notebook_dir = workspace_root / "notebooks"
    notebook_dir.mkdir(parents=True)

    config = {
        "working_dir": str(tmp_path / "external_workspace"),
        "featurization_output_dir": "featurization",
        "metadata_file": "sba_loans_metadata_table.csv",
        "featurization_input_data": "sba_loans_user_cleaned.csv",
    }
    with open(workspace_root / "featurizer_config.yaml", "w", encoding="utf-8") as fh:
        yaml.safe_dump(config, fh)

    resolver = build_notebook_resolver(str(notebook_dir))

    assert os.path.abspath(resolver.working_dir) == os.path.abspath(str(tmp_path / "external_workspace"))
    assert resolver.metadata_file == "sba_loans_metadata_table.csv"
