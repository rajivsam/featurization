import os
import yaml

def initialize_config(working_dir: str, metadata_file: str, data_file: str, structural_type: str = "cross-sectional", config_name: str = "featurizer_config.yaml"):
    """
    Bootstraps a new featurization workspace by persisting key project anchors 
    from dd-parser-cleaner into the featurizer_config.yaml.
    """
    abs_working_dir = os.path.abspath(working_dir)
    config_path = os.path.join(abs_working_dir, config_name)

    # 1. Load existing config if available (check target path or current directory)
    existing_config = {}
    search_path = config_path if os.path.exists(config_path) else config_name
    if os.path.exists(search_path):
        with open(search_path, "r") as f:
            existing_config = yaml.safe_load(f) or {}

    # 2. Define final config, preferring existing values for non-anchor settings
    final_config = {
        "working_dir": abs_working_dir,
        "pipeline": existing_config.get("pipeline", []), # New pipeline structure
        "metadata_file": metadata_file,
        "dd_cleaner_output_dir": existing_config.get("dd_cleaner_output_dir", "dd_cleaner"),
        "featurization_input_data": existing_config.get("featurization_input_data", data_file),
        "featurization_output_dir": existing_config.get("featurization_output_dir", "featurization"),
        "quarantine_dir": existing_config.get("quarantine_dir", "featurization/quarantine"),
        "featurized_data_file": existing_config.get("featurized_data_file", "featurized_data.csv"),
        "model_ready_data_file": existing_config.get("model_ready_data_file", "model_ready_numeric_data.csv"),
        "feat_doc_directory": existing_config.get("feat_doc_directory", "featurization_docs"),
        "entity_assignment_output": existing_config.get("entity_assignment_output", "entity_assignments.md"),
        "script_dir": existing_config.get("script_dir", "featurization_scripts"), # New script directory key
        "script_name": existing_config.get("script_name", "featurization.py"),   # New script file name key
        "country_code": existing_config.get("country_code", "us"),
        "structural_type": structural_type,
        "VALIDATION_SIZE": existing_config.get("VALIDATION_SIZE", 0.2),
        "FEATURE_SELECTION_MIN_NON_NULL_RATE": existing_config.get(
            "FEATURE_SELECTION_MIN_NON_NULL_RATE", 0.01
        ),
        "MODEL_READY_NUMERIC_ONLY": existing_config.get("MODEL_READY_NUMERIC_ONLY", True)
    }

    # 3. Preserve any custom stage definitions or extra settings from the existing config
    for key, value in existing_config.items():
        if key not in final_config:
            final_config[key] = value
    
    # 4. Ensure standard directory structure exists relative to finalized working_dir
    required_dirs = [
        "data",
        "documents",
        "notebooks",
        "featurization_scripts",
        os.path.join("data", final_config["dd_cleaner_output_dir"]),
        os.path.join("data", final_config["featurization_output_dir"]),
        os.path.join("data", final_config["quarantine_dir"]),
        os.path.join("documents", final_config["feat_doc_directory"])
    ]
    for folder in required_dirs:
        os.makedirs(os.path.join(abs_working_dir, folder), exist_ok=True)
    
    with open(config_path, "w") as f:
        yaml.safe_dump(final_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✨ Workspace Initialized: {config_path}")
    print(f"   - Metadata Anchor: {metadata_file}")
    print(f"   - Cleaned Data Anchor: {data_file}")