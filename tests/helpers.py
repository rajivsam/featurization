import os
import yaml


def load_workspace_config() -> dict:
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "featurizer_config.yaml")
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_workspace_dir() -> str:
    config = load_workspace_config()
    return config["working_dir"]
