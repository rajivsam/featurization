import os
import yaml

from featurization.core.featurization_init import initialize_config
from featurization.core.path_coordinator import PathCoordinator
from featurization.core.data_loader import KMDSDataLoader
from tests.helpers import get_workspace_dir, load_workspace_config

def test_workspace_init():
    # 1. Define Test Parameters from repository configuration
    config = load_workspace_config()
    working_dir = get_workspace_dir()
    metadata_file = config.get("metadata_file", "sba_loans_metadata_table.csv")
    data_file = config.get("featurization_input_data", "sba_loans_user_cleaned.csv")
    config_name = "featurizer_config.yaml"
    
    print(f"🧪 Testing Initialization for: {working_dir}")
    
    # 2. Execute Initialization
    initialize_config(
        working_dir=working_dir,
        metadata_file=metadata_file,
        data_file=data_file,
        config_name=config_name
    )
    
    # 3. Load generated config
    config_path = os.path.join(working_dir, config_name)
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    # 4. Verify Directory Structure Creation
    print("\n📁 Validating Directory Structure Creation:")
    required_dirs = ["data", "documents", "notebooks", "featurization_scripts"]
    for folder in required_dirs:
        dir_path = os.path.join(working_dir, folder)
        is_present = os.path.isdir(dir_path)
        print(f"   - {folder}: {'✅' if is_present else '❌'}")
        assert is_present, f"Directory {folder} was not created during initialization."

    # 5. Initialize PathCoordinator
    resolver = PathCoordinator(working_dir=working_dir, config=config)
    
    # 6. Assertions and Validation
    print("\n🔍 Validating PathCoordinator Properties:")
    print(f"   - Metadata File: {resolver.metadata_file}")
    print(f"   - Input Data File: {resolver.featurization_input_data}")
    print(f"   - Metadata Path: {resolver.metadata_path}")
    print(f"   - Input Data Path: {resolver.featurization_input_path}")
    print(f"   - Scripts Path: {resolver.scripts_path}")
    print(f"   - Initialized Status: {resolver.initialized}")
    
    # Define absolute expected paths based on PathCoordinator's logic
    expected_meta = os.path.join(working_dir, "data", "dd_cleaner", resolver.metadata_file)
    expected_data = os.path.join(working_dir, "data", "dd_cleaner", resolver.featurization_input_data)
    expected_scripts = os.path.join(working_dir, "featurization_scripts")
    
    # Assert exact absolute path matches
    assert resolver.metadata_path == expected_meta
    assert resolver.featurization_input_path == expected_data
    assert resolver.scripts_path == expected_scripts
    assert resolver.initialized is True

    # 7. Verify Data Loading
    print("\n📊 Validating Data Loading via KMDSDataLoader:")
    loader = KMDSDataLoader(resolver)
    
    # Attempt to load data and metadata
    loaded_data = loader.data
    loaded_metadata = loader.metadata
    
    print(f"   - Cleaned Data Shape: {loaded_data.shape}")
    print(f"   - Metadata Shape: {loaded_metadata.shape}")
    assert not loaded_data.empty, "Loaded cleaned data should not be empty."
    assert not loaded_metadata.empty, "Loaded metadata should not be empty."
    
    print("\n✅ Initialization Test Passed: Config persisted, directories created, and properties resolved correctly.")

def test_initialize_config_normalizes_temporal_structural_type(tmp_path):
    working_dir = tmp_path / "workspace_temporal"
    metadata_file = "metadata.csv"
    data_file = "data.csv"

    initialize_config(
        working_dir=str(working_dir),
        metadata_file=metadata_file,
        data_file=data_file,
        structural_type="event-log",
    )

    config_path = os.path.join(str(working_dir), "featurizer_config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["structural_type"] == "temporal"


def test_initialize_config_normalizes_wide_and_short_structural_type(tmp_path):
    working_dir = tmp_path / "workspace_wide_short"
    metadata_file = "metadata.csv"
    data_file = "data.csv"

    initialize_config(
        working_dir=str(working_dir),
        metadata_file=metadata_file,
        data_file=data_file,
        structural_type="wide-and-short",
    )

    config_path = os.path.join(str(working_dir), "featurizer_config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config["structural_type"] == "wide and short"


def test_path_coordinator_strips_redundant_data_prefixes(tmp_path):
    working_dir = str(tmp_path)
    config = {
        "featurization_output_dir": "data/data/featurization",
        "dd_cleaner_output_dir": "data/data/dd_cleaner",
        "metadata_file": "metadata.csv",
        "featurization_input_data": "data.csv",
    }

    resolver = PathCoordinator(working_dir=working_dir, config=config)

    assert resolver.featurized_dataset_path == os.path.join(working_dir, "data", "featurization", "featurized_data.csv")
    assert resolver.model_ready_dataset_path == os.path.join(working_dir, "data", "featurization", "model_ready_numeric_data.csv")
    assert resolver.metadata_path == os.path.join(working_dir, "data", "dd_cleaner", "metadata.csv")
    assert resolver.featurization_input_path == os.path.join(working_dir, "data", "dd_cleaner", "data.csv")


if __name__ == "__main__":
    test_workspace_init()