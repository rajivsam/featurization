# KMDS Featurization

This repository provides a configurable, stage-based featurization engine for SBA modeling workflows.

The design goal is simple:
- keep stage logic understandable and composable
- keep orchestration/configuration centralized
- keep modeling flow leakage-safe (fit on train only, reuse on val/active)

## What This Produces

The pipeline writes two CSV outputs:
- featurized_data.csv: consolidated engineered dataset (modeled + active partitions)
- model_ready_numeric_data.csv: numeric model-ready export from the final stage output

For the current SBA flow, the model-ready dataset is:
- numeric/bool only
- train-fitted feature-selected
- schema-aligned across train/val/active

## Core Concepts

- Anchor index: record_id
- Stage contract: method(context, stage_cfg) -> DataFrame
- Waterfall behavior: each stage can shrink survivor rows by index
- Horizontal feature assembly: stage outputs are concatenated by index
- Controlled index expansion: only stages marked allow_new_indices may re-introduce rows

## Pipeline Layout (Current Hybrid Design)

Front section (feature assembly):
1. record_id_definition
2. borrower_geo_coding
3. prepare_categorical_data
4. prepare_numerical_data
5. merge_categorical_and_numerical
6. merge_with_borrower_geo

Merge stage design:
- package component: src/tabular/merge_ops.py
- user wrappers: featurization_scripts/featurization.py
- merge key: record_id index

Leakage-safe modeling section:
7. low_count_featurization_of_cat_vars
8. hierarchical_low_count_var_encoding
9. loan_status_recoding
10. filter_modeling_universe
11. stratified_train_val_split
12. target_encode_categorical_vars
13. harmonize_and_project_feature_space
14. merge_modeled_and_active_partitions

## Tree-Based Feature Selection

Feature selection runs in harmonize_and_project_feature_space using train rows only.

Supported selector modes:
- threshold
- tree_ensemble

Supported tree models:
- gbm
- random_forest
- xgboost (optional dependency)

All selector choices are config-driven via featurizer_config.yaml and surfaced through PathCoordinator (no stage-level hardcoded constants).

## Repository Organization

- src/featurization/core: orchestration, configuration bootstrap, path resolution
- src/featurization/transforms: reusable transformation primitives
- src/tabular: reusable tabular feature modules (encoding, splitting, feature space)
- src/tabular/merge_ops.py: reusable index-aligned tabular merge helper
- tests: package-level smoke and behavior checks
- documents: architecture and configuration references

## Package Component Buckets

The tabular package modules are intentionally split into two modeling buckets:

- Row-selection components:
	- src/tabular/modeling_filter.py
	- src/tabular/train_val_split.py
	- Purpose: decide which records participate in training and how records are partitioned.

- Column-selection components:
	- src/tabular/feature_space.py
	- src/tabular/target_encoding.py
	- src/tabular/low_count_cat_var_encoding.py
	- src/tabular/hierarchical_low_count_var_encoding.py
	- Purpose: decide which feature columns are engineered, selected, encoded, and projected.

- Assembly components:
	- src/tabular/merge_ops.py
	- Purpose: index-aligned horizontal composition of prepared payloads.

## CLI

Initialize config:

```bash
featurization-cli init \
  --working-dir /path/to/workspace \
  --metadata-file sba_loans_metadata_table.csv \
  --data-file sba_loans_user_cleaned.csv
```

Run pipeline:

```bash
featurization-cli run --working-dir /path/to/workspace
```

Run smoke test in this repo:

```bash
pytest -q tests/test_sba_pipeline.py
```

## How To Extend Safely

1. Add reusable logic in src/tabular first whenever possible.
2. Keep stage wrappers in workspace featurization_scripts/featurization.py thin and explicit.
3. Add new tunables to:
	- featurizer_config.yaml
	- src/featurization/core/path_coordinator.py
	- src/featurization/core/featurization_init.py
4. Preserve leakage rules:
	- fit artifacts on train only
	- transform val/active using train-fitted artifacts
5. Validate with tests after each change.

## Recommended Read Order

1. documents/sba_pipeline_featurization.md
2. documents/config_blueprint.md
3. documents/path_coordinator_function.md
4. src/featurization/core/sequential_pipeline_runner.py
5. src/tabular/feature_space.py
