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
        "FEATURE_SELECTION_METHOD": existing_config.get("FEATURE_SELECTION_METHOD", "tree_ensemble"),
        "FEATURE_SELECTION_TOP_K": existing_config.get("FEATURE_SELECTION_TOP_K", 50),
        "FEATURE_SELECTION_TOP_K_MODE": existing_config.get("FEATURE_SELECTION_TOP_K_MODE", "fixed"),
        "FEATURE_SELECTION_TOP_K_MIN": existing_config.get("FEATURE_SELECTION_TOP_K_MIN", 1),
        "FEATURE_SELECTION_TOP_K_MIN_RATIO": existing_config.get(
            "FEATURE_SELECTION_TOP_K_MIN_RATIO", 0.0
        ),
        "FEATURE_SELECTION_MIN_FEATURE_COUNT": existing_config.get(
            "FEATURE_SELECTION_MIN_FEATURE_COUNT", 0
        ),
        "FEATURE_SELECTION_TOP_K_MAX": existing_config.get("FEATURE_SELECTION_TOP_K_MAX", 0),
        "FEATURE_SELECTION_TARGET_FEATURE_COUNT": existing_config.get(
            "FEATURE_SELECTION_TARGET_FEATURE_COUNT", 0
        ),
        "FEATURE_SELECTION_KNEEDLE_SENSITIVITY": existing_config.get(
            "FEATURE_SELECTION_KNEEDLE_SENSITIVITY", 1.0
        ),
        "FEATURE_SELECTION_KNEEDLE_CURVE": existing_config.get(
            "FEATURE_SELECTION_KNEEDLE_CURVE", "convex"
        ),
        "FEATURE_SELECTION_KNEEDLE_DIRECTION": existing_config.get(
            "FEATURE_SELECTION_KNEEDLE_DIRECTION", "decreasing"
        ),
        "FEATURE_SELECTION_REQUIRE_KNEEDLE": existing_config.get(
            "FEATURE_SELECTION_REQUIRE_KNEEDLE", False
        ),
        "FEATURE_SELECTION_IMPORTANCE_FLOOR": existing_config.get(
            "FEATURE_SELECTION_IMPORTANCE_FLOOR", 0.0
        ),
        "FEATURE_SELECTION_TREE_MODEL": existing_config.get("FEATURE_SELECTION_TREE_MODEL", "gbm"),
        "FEATURE_SELECTION_TREE_N_ESTIMATORS": existing_config.get(
            "FEATURE_SELECTION_TREE_N_ESTIMATORS", 200
        ),
        "FEATURE_SELECTION_TREE_LEARNING_RATE": existing_config.get(
            "FEATURE_SELECTION_TREE_LEARNING_RATE", 0.05
        ),
        "FEATURE_SELECTION_TREE_MAX_DEPTH": existing_config.get("FEATURE_SELECTION_TREE_MAX_DEPTH", 3),
        "FEATURE_SELECTION_TREE_SUBSAMPLE": existing_config.get(
            "FEATURE_SELECTION_TREE_SUBSAMPLE", 0.8
        ),
        "FEATURE_SELECTION_TREE_RANDOM_STATE": existing_config.get(
            "FEATURE_SELECTION_TREE_RANDOM_STATE", 42
        ),
        "MODEL_READY_NUMERIC_ONLY": existing_config.get("MODEL_READY_NUMERIC_ONLY", True),
        "feature_selection_knee_curve_file": existing_config.get(
            "feature_selection_knee_curve_file", "feature_selection_knee_curve.png"
        ),
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


def bootstrap_provisional_config(
    working_dir: str,
    metadata_file: str = "your_metadata.csv",
    data_file: str = "your_cleaned_data.csv",
    structural_type: str = "cross-sectional",
    config_name: str = "provisional_featurization_config.yaml",
    overwrite: bool = False,
) -> str:
    """Write a starter provisional featurization config file for a new project."""
    abs_working_dir = os.path.abspath(working_dir)
    os.makedirs(abs_working_dir, exist_ok=True)
    config_path = os.path.join(abs_working_dir, config_name)

    if os.path.exists(config_path) and not overwrite:
        raise FileExistsError(
            f"Provisional config already exists: {config_path}. Use overwrite=True to replace it."
        )

    template = f"""# Provisional featurization starter config
# Update the anchors and pipeline definitions for your project.

working_dir: "{abs_working_dir}"
structural_type: "{structural_type}"
country_code: "us"

# Where cleaned data is written by your upstream preprocessing flow
dd_cleaner_output_dir: "dd_cleaner"
metadata_file: "{metadata_file}"
featurization_input_data: "{data_file}"

# Where featurization logic and stage wrappers live
script_dir: "featurization_scripts"
script_name: "featurization.py"

# Output artifacts produced by the featurization pipeline
featurization_output_dir: "featurization"
featurized_data_file: "featurized_data.csv"
model_ready_data_file: "model_ready_numeric_data.csv"
quarantine_dir: "featurization/quarantine"
feat_doc_directory: "featurization_docs"

# Modeling and feature-selection defaults
MIN_SUPPORT_THRESHOLD_CAT_VARS: 5
VALIDATION_SIZE: 0.2
FEATURE_SELECTION_MIN_NON_NULL_RATE: 0.01
FEATURE_SELECTION_METHOD: "tree_ensemble"
FEATURE_SELECTION_TOP_K: 50
FEATURE_SELECTION_TOP_K_MODE: "fixed"
FEATURE_SELECTION_TOP_K_MIN: 1
FEATURE_SELECTION_TOP_K_MIN_RATIO: 0.0
FEATURE_SELECTION_MIN_FEATURE_COUNT: 0
FEATURE_SELECTION_TOP_K_MAX: 0
FEATURE_SELECTION_TARGET_FEATURE_COUNT: 0
FEATURE_SELECTION_KNEEDLE_SENSITIVITY: 1.0
FEATURE_SELECTION_KNEEDLE_CURVE: "convex"
FEATURE_SELECTION_KNEEDLE_DIRECTION: "decreasing"
FEATURE_SELECTION_REQUIRE_KNEEDLE: false
FEATURE_SELECTION_IMPORTANCE_FLOOR: 0.0
FEATURE_SELECTION_TREE_MODEL: "gbm"
FEATURE_SELECTION_TREE_N_ESTIMATORS: 200
FEATURE_SELECTION_TREE_LEARNING_RATE: 0.05
FEATURE_SELECTION_TREE_MAX_DEPTH: 3
FEATURE_SELECTION_TREE_SUBSAMPLE: 0.8
FEATURE_SELECTION_TREE_RANDOM_STATE: 42
MODEL_READY_NUMERIC_ONLY: true

# Pipeline: ordered list of stage dictionaries
pipeline:
  - name: "Example Feature Stage"
    method: "example_feature_stage"
    entity: "System"
    sub_filter: "example"
    allow_new_indices: false
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"✨ Provisional config created: {config_path}")
    return config_path
