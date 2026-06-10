# Configuration Guide: featurizer_config.yaml Blueprint

This document explains the active configuration contract used by the featurization engine.

## 1. Configuration Model

featurizer_config.yaml is the single runtime source of truth for:
- path routing
- pipeline stage order
- transformation and modeling constants

The file uses a flat key structure plus a pipeline list.

## 2. Key Sections

Global and path keys:
- working_dir
- structural_type
- country_code
- dd_cleaner_output_dir
- metadata_file
- featurization_input_data
- featurization_output_dir
- featurized_data_file
- model_ready_data_file
- quarantine_dir
- script_dir
- script_name

Modeling constants:
- MIN_SUPPORT_THRESHOLD_CAT_VARS
- VALIDATION_SIZE
- FEATURE_SELECTION_MIN_NON_NULL_RATE
- MODEL_READY_NUMERIC_ONLY

Tree-based feature selection keys:
- FEATURE_SELECTION_METHOD
- FEATURE_SELECTION_TOP_K
- FEATURE_SELECTION_IMPORTANCE_FLOOR
- FEATURE_SELECTION_TREE_MODEL
- FEATURE_SELECTION_TREE_N_ESTIMATORS
- FEATURE_SELECTION_TREE_LEARNING_RATE
- FEATURE_SELECTION_TREE_MAX_DEPTH
- FEATURE_SELECTION_TREE_SUBSAMPLE
- FEATURE_SELECTION_TREE_RANDOM_STATE

Pipeline orchestration:
- pipeline: ordered list of stage dictionaries

## 3. Current Pipeline Template

```yaml
working_dir: "/path/to/workspace"
structural_type: "cross-sectional"
country_code: "us"

dd_cleaner_output_dir: "dd_cleaner"
metadata_file: "sba_loans_metadata_table.csv"
featurization_input_data: "sba_loans_user_cleaned.csv"

script_dir: "featurization_scripts"
script_name: "featurization.py"

featurization_output_dir: "featurization"
featurized_data_file: "featurized_data.csv"
model_ready_data_file: "model_ready_numeric_data.csv"
quarantine_dir: "featurization/quarantine"

MIN_SUPPORT_THRESHOLD_CAT_VARS: 5
VALIDATION_SIZE: 0.2
FEATURE_SELECTION_MIN_NON_NULL_RATE: 0.01

FEATURE_SELECTION_METHOD: "tree_ensemble"
FEATURE_SELECTION_TOP_K: 50
FEATURE_SELECTION_IMPORTANCE_FLOOR: 0.0
FEATURE_SELECTION_TREE_MODEL: "gbm"
FEATURE_SELECTION_TREE_N_ESTIMATORS: 200
FEATURE_SELECTION_TREE_LEARNING_RATE: 0.05
FEATURE_SELECTION_TREE_MAX_DEPTH: 3
FEATURE_SELECTION_TREE_SUBSAMPLE: 0.8
FEATURE_SELECTION_TREE_RANDOM_STATE: 42

MODEL_READY_NUMERIC_ONLY: true

pipeline:
  - name: "Record ID Generation"
    method: "record_id_definition"
    entity: "System"
    sub_filter: "System"

  - name: "Borrower Geo Coding"
    method: "borrower_geo_coding"
    entity: "geographic"
    sub_filter: "Borrower"

  - name: "Prepare Categorical Data"
    method: "prepare_categorical_data"
    entity: "categorical"
    sub_filter: "modeling"

  - name: "Prepare Numerical Data"
    method: "prepare_numerical_data"
    entity: "numerical"
    sub_filter: "modeling"

  - name: "Merge Categorical And Numerical"
    method: "merge_categorical_and_numerical"
    entity: "System"
    sub_filter: "merge"

  - name: "Merge With Borrower Geo"
    method: "merge_with_borrower_geo"
    entity: "System"
    sub_filter: "merge"

  - name: "Low Count Categorical Encoding"
    method: "low_count_featurization_of_cat_vars"
    entity: "categorical"
    sub_filter: "low_count"

  - name: "Hierarchical NAICS Recoding"
    method: "hierarchical_low_count_var_encoding"
    entity: "categorical"
    sub_filter: "naics"

  - name: "Loan Status Recoding"
    method: "loan_status_recoding"
    entity: "System"
    sub_filter: "Loan"

  - name: "Filter Modeling Universe"
    method: "filter_modeling_universe"
    entity: "System"
    sub_filter: "Loan"

  - name: "Train Validation Split"
    method: "stratified_train_val_split"
    entity: "System"
    sub_filter: "Loan"

  - name: "Target Encode Categoricals"
    method: "target_encode_categorical_vars"
    entity: "categorical"
    sub_filter: "modeling"

  - name: "Harmonize And Project Feature Space"
    method: "harmonize_and_project_feature_space"
    entity: "System"
    sub_filter: "modeling"

  - name: "Merge Modeled And Active Partitions"
    method: "merge_modeled_and_active_partitions"
    entity: "System"
    sub_filter: "modeling"
    allow_new_indices: true
```

## 4. Extension Rule (Important)

When introducing any new tunable, wire it in three places:
1. featurizer_config.yaml
2. src/featurization/core/path_coordinator.py
3. src/featurization/core/featurization_init.py

This keeps stage code free of hidden constants and ensures reproducibility.