import os
import yaml

from featurization.core.featurization_init import initialize_config
from featurization.core.path_coordinator import PathCoordinator
from featurization.utils import get_entity_list
from tests.helpers import get_workspace_dir, load_workspace_config

def test_real_data_entity_extraction():
    """
    Validates get_entity_list utility using real data parameters.
    Adheres to Principle #1: No Mocking.
    """
    # 1. Define Real Data Parameters from repository configuration
    config = load_workspace_config()
    working_dir = get_workspace_dir()
    metadata_file = config.get("metadata_file", "sba_loans_metadata_table.csv")
    data_file = config.get("featurization_input_data", "sba_loans_user_cleaned.csv")
    
    print(f"🧪 Testing Entity List Extraction on Real Data: {working_dir}")
    
    # 2. Ensure Environment is Initialized
    if not os.path.exists(os.path.join(working_dir, "featurizer_config.yaml")):
        initialize_config(working_dir, metadata_file, data_file)

    with open(os.path.join(working_dir, "featurizer_config.yaml"), "r") as f:
        config = yaml.safe_load(f)

    # 3. Initialize PathCoordinator
    resolver = PathCoordinator(working_dir=working_dir, config=config)
    
    # 4. Execute Utility
    entities = get_entity_list(resolver)
    
    # 5. Validation
    print(f"\n🔍 Discovered Entities in Metadata:")
    for entity in entities:
        print(f"   - {entity}")

    assert isinstance(entities, list), "Utility should return a list."
    assert len(entities) > 0, f"Expected entities in real metadata table: {resolver.metadata_path}"
    
    print(f"\n✅ Utility Test Passed: {len(entities)} unique entities extracted from real data.")

if __name__ == "__main__":
    test_real_data_entity_extraction()