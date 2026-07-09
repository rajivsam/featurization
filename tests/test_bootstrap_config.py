import os
import yaml

from featurization.core.featurization_init import bootstrap_provisional_config


def test_bootstrap_creates_provisional_config(tmp_path):
    working_dir = tmp_path / "workspace"
    config_name = "provisional_featurization_config.yaml"
    metadata_file = "example_metadata.csv"
    data_file = "example_data.csv"

    config_path = bootstrap_provisional_config(
        working_dir=str(working_dir),
        metadata_file=metadata_file,
        data_file=data_file,
        structural_type="panel",
        config_name=config_name,
        overwrite=False,
    )

    assert os.path.exists(config_path)
    assert config_path.endswith(config_name)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["working_dir"] == os.path.abspath(str(working_dir))
    assert config["structural_type"] == "panel"
    assert config["metadata_file"] == metadata_file
    assert config["featurization_input_data"] == data_file
    assert isinstance(config.get("pipeline"), list)
    assert len(config["pipeline"]) == 1
    assert config["pipeline"][0]["method"] == "example_feature_stage"


def test_bootstrap_refuses_existing_config_without_overwrite(tmp_path):
    working_dir = tmp_path / "workspace"
    config_name = "provisional_featurization_config.yaml"

    bootstrap_provisional_config(
        working_dir=str(working_dir),
        config_name=config_name,
    )

    try:
        bootstrap_provisional_config(
            working_dir=str(working_dir),
            config_name=config_name,
            overwrite=False,
        )
        assert False, "Expected FileExistsError when existing config exists without overwrite"
    except FileExistsError:
        pass


def test_bootstrap_command_creates_config(monkeypatch, capsys, tmp_path):
    import sys

    working_dir = tmp_path / "workspace_cli"
    metadata_file = "cli_metadata.csv"
    data_file = "cli_data.csv"
    config_name = "provisional_featurization_config.yaml"

    monkeypatch.setattr(sys, "argv", [
        "featurization-cli",
        "bootstrap",
        "--working-dir",
        str(working_dir),
        "--metadata-file",
        metadata_file,
        "--data-file",
        data_file,
        "--config-name",
        config_name,
    ])

    from featurization.cli import main

    main()

    captured = capsys.readouterr()
    assert "✅ Provisional config written" in captured.out

    config_path = working_dir / config_name
    assert config_path.exists()

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["metadata_file"] == metadata_file
    assert config["featurization_input_data"] == data_file


def test_bootstrap_command_overwrites_existing_config(monkeypatch, capsys, tmp_path):
    import sys

    working_dir = tmp_path / "workspace_cli_overwrite"
    metadata_file = "cli_metadata.csv"
    data_file = "cli_data.csv"
    config_name = "provisional_featurization_config.yaml"

    # Create first provisional config.
    monkeypatch.setattr(sys, "argv", [
        "featurization-cli",
        "bootstrap",
        "--working-dir",
        str(working_dir),
        "--metadata-file",
        metadata_file,
        "--data-file",
        data_file,
        "--config-name",
        config_name,
    ])
    from featurization.cli import main
    main()

    # Re-run with overwrite enabled and a different metadata placeholder.
    new_metadata = "cli_metadata_replaced.csv"
    monkeypatch.setattr(sys, "argv", [
        "featurization-cli",
        "bootstrap",
        "--working-dir",
        str(working_dir),
        "--metadata-file",
        new_metadata,
        "--data-file",
        data_file,
        "--config-name",
        config_name,
        "--overwrite",
    ])
    main()

    captured = capsys.readouterr()
    assert "✅ Provisional config written" in captured.out

    config_path = working_dir / config_name
    assert config_path.exists()

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["metadata_file"] == new_metadata
    assert config["featurization_input_data"] == data_file


def test_bootstrap_normalizes_temporal_structural_type(tmp_path):
    working_dir = tmp_path / "workspace_temporal"
    config_path = bootstrap_provisional_config(
        working_dir=str(working_dir),
        structural_type="event log",
        overwrite=True,
    )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["structural_type"] == "temporal"


def test_bootstrap_normalizes_wide_and_short_structural_type(tmp_path):
    working_dir = tmp_path / "workspace_wide_short"
    config_path = bootstrap_provisional_config(
        working_dir=str(working_dir),
        structural_type="wide-and-short",
        overwrite=True,
    )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["structural_type"] == "wide and short"
