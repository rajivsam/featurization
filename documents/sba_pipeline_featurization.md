# SBA Featurization Pipeline: End-to-End Stage Specification

## 1. Architecture Summary
The SBA pipeline uses an index-centric waterfall contract.

- Universal anchor: record_id index.
- Stage signature: method(context, stage_cfg) -> DataFrame.
- Default index rule: each stage returns rows from the current survivor universe.
- Merge rule: stage outputs are concatenated horizontally by index.
- Controlled exception: only stages configured with allow_new_indices can re-introduce rows.

Core intent:
- Modeling development is performed on non-active rows (loan_status_r in {0, 1}).
- Active rows (loan_status_r = -1) are held out, transformed with train-fitted artifacts, then merged back in aligned schema.

## 2. Configuration Anchors
Key fields in featurizer_config.yaml:

- MIN_SUPPORT_THRESHOLD_CAT_VARS
- VALIDATION_SIZE
- FEATURE_SELECTION_MIN_NON_NULL_RATE
- FEATURE_SELECTION_METHOD
- FEATURE_SELECTION_TREE_MODEL
- FEATURE_SELECTION_TOP_K
- FEATURE_SELECTION_TOP_K_MODE
- FEATURE_SELECTION_TOP_K_MIN_RATIO
- FEATURE_SELECTION_MIN_FEATURE_COUNT
- FEATURE_SELECTION_TARGET_FEATURE_COUNT
- FEATURE_SELECTION_REQUIRE_KNEEDLE
- FEATURE_SELECTION_IMPORTANCE_FLOOR
- FEATURE_SELECTION_TREE_N_ESTIMATORS
- FEATURE_SELECTION_TREE_LEARNING_RATE
- FEATURE_SELECTION_TREE_MAX_DEPTH
- FEATURE_SELECTION_TREE_SUBSAMPLE
- FEATURE_SELECTION_TREE_RANDOM_STATE

Important file/path anchors:
- Input data: data/dd_cleaner/sba_loans_user_cleaned.csv
- Metadata: data/dd_cleaner/sba_loans_metadata_table.csv
- User stage logic: featurization_scripts/featurization.py

## 2.1. Provisional Config Bootstrap
A starter provisional configuration can be generated via the package CLI. This writes a `provisional_featurization_config.yaml` file with placeholder anchors and a sample pipeline stage.

Example:

```bash
featurization-cli bootstrap \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv
```

To replace an existing provisional config file, add `--overwrite`:

```bash
featurization-cli bootstrap \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv \
  --overwrite
```

After bootstrap, revise the generated YAML to match project-specific paths, file names, and staged transformation logic.

## 3. Stage Sequence (Current)

Feature-assembly front section:

### Stage 1: record_id_definition
Creates record_id when absent and promotes it to index.

### Stage 2: borrower_geo_coding
Adds borrower_latitude and borrower_longitude using fallback ZIP -> CITY -> STATE centroid.
Borrower geo attributes are sourced from metadata tagging via get_stage_subset(..., entity="geographic", sub_filter="Borrower").

### Stage 3: prepare_categorical_data
Builds categorical payload for modeling and stores it in context.

### Stage 4: prepare_numerical_data
Builds numeric payload for modeling and stores it in context.

### Stage 5: merge_categorical_and_numerical
Merges categorical and numerical payloads by record_id index.
Implementation uses package helper src/tabular/merge_ops.py.

### Stage 6: merge_with_borrower_geo
Merges the structured payload with borrower geo features by record_id index.
Implementation uses package helper src/tabular/merge_ops.py.

Leakage-safe modeling section:

### Stage 7: low_count_featurization_of_cat_vars
Two-pass categorical low-support handling with _rcs output suffix.

### Stage 8: hierarchical_low_count_var_encoding
NAICS-specific hierarchical support recoding (right-mask strategy).

### Stage 9: loan_status_recoding
Maps operational status labels into {-1, 0, 1}.

### Stage 10: filter_modeling_universe
Removes active class from modeling survivors and stores active rows in context["active_holdout"].
This is a row-selection stage, not a feature-selection stage.

### Stage 11: stratified_train_val_split
Creates dataset_split = train/val with stratification by loan_status_r.

### Stage 12: target_encode_categorical_vars
Fits TargetEncoder on train only; transforms modeling and active with train-fitted artifact.

Current safeguards:
- stage requires explicit exclusion policy (exclude_cols and/or exclude_name_patterns)
- borrower geographic source subset is excluded before encoding
- when raw and _rcs categorical variants both exist, only _rcs variants are encoded

### Stage 13: harmonize_and_project_feature_space
Selects canonical feature schema from train partition and projects modeled + active partitions.

Feature selection behavior:
- threshold mode: non-null and uniqueness constraints
- tree_ensemble mode: supervised importance ranking using gbm/random_forest/xgboost
- always fit on train only
- top-k can be fixed or kneedle-driven
- supports conservative ratio floor and explicit target feature count override
- strict kneedle mode can fail fast and require manual DS review if knee is unstable

Diagnostics:
- prints feature-selection summary (candidate count, selected count, k, mode)
- saves feature importance knee-curve image to featurization output directory

### Stage 14: merge_modeled_and_active_partitions
Concatenates projected modeled and active partitions into one aligned output.

## 4. Artifact and Leakage Rules

Fit-on-train-only artifacts:
- target encoder
- feature-selection model and selected feature list

Transform-only for validation and active:
- no refit on val or active

Merge reconciliation:
- partition row counts may differ
- feature columns must match before final merge

## 5. Output Semantics
Final persisted output (featurized_data.csv) includes:
- engineered feature columns
- loan_status_r
- dataset_split (train, val, active)
- dataset_partition (modeled, active)

Final model-ready export (model_ready_numeric_data.csv):
- numeric and bool columns only
- built from final stage output

CSV persistence behavior:
- featurized_data.csv and model_ready_numeric_data.csv are written with index=False
- no record_id/Unnamed index artifact columns are persisted

## 6. Code Map

Package component taxonomy:

- Row-selection modules:
  - src/tabular/modeling_filter.py
  - src/tabular/train_val_split.py

- Column-selection modules:
  - src/tabular/feature_space.py
  - src/tabular/target_encoding.py
  - src/tabular/low_count_cat_var_encoding.py
  - src/tabular/hierarchical_low_count_var_encoding.py

- Assembly module:
  - src/tabular/merge_ops.py

Package reusable modules:
- src/tabular/low_count_cat_var_encoding.py
- src/tabular/hierarchical_low_count_var_encoding.py
- src/tabular/modeling_filter.py
- src/tabular/train_val_split.py
- src/tabular/target_encoding.py
- src/tabular/feature_space.py
- src/tabular/merge_ops.py

Workspace stage wrapper:
- featurization_scripts/featurization.py

Core orchestration and config plumbing:
- src/featurization/core/sequential_pipeline_runner.py
- src/featurization/core/path_coordinator.py
- src/featurization/core/featurization_init.py

## 7. Validation Coverage
Primary smoke/integration test:
- tests/test_sba_pipeline.py

Current checks include:
- expected stage methods in pipeline
- expected engineered columns
- binary modeled target universe
- split and partition markers
- persisted output artifacts exist and contain required fields

## 8. Extension Guidance
- Keep stage wrappers thin and explicit.
- Put reusable transformations in src/tabular.
- Add any new tuning parameter in three places:
  - featurizer_config.yaml
  - src/featurization/core/path_coordinator.py
  - src/featurization/core/featurization_init.py
- Preserve leakage controls when introducing new modeling artifacts.
