# KMDS Featurization

This repository provides a configurable, stage-based featurization package for KMDS project datasets.

It is designed to be dataset-agnostic at the package level:

- stage orchestration is generic and configuration-driven
- reusable feature logic lives in package modules
- modeling flow remains leakage-safe (fit on train only, reuse on val/active)

SBA-specific file names and stage examples in this repo are reference defaults, not a package constraint.

## What This Produces

The pipeline writes two CSV outputs:

- featurized_data.csv: consolidated engineered dataset
- model_ready_numeric_data.csv: numeric model-ready export from the final stage output

Additional diagnostic artifact:

- feature_selection_knee_curve.png: ranked feature-importance knee plot in the featurization output directory

Model-ready output behavior:

- numeric and bool columns only
- train-fitted feature-selected schema
- aligned schema across modeled and active partitions
- persisted with index=False to avoid index artifact columns

## Core Runtime Contract

- Anchor index: record_id
- Stage contract: method(context, stage_cfg) -> DataFrame
- Waterfall behavior: each stage can reduce the survivor universe by index
- Horizontal assembly: stage outputs are concatenated by index
- Controlled expansion: only stages with allow_new_indices may intentionally re-introduce rows

## Package Architecture

Core orchestration:

- src/featurization/core/sequential_pipeline_runner.py
- src/featurization/core/path_coordinator.py
- src/featurization/core/featurization_init.py

Reusable tabular modules:

- src/tabular/modeling_filter.py
- src/tabular/train_val_split.py
- src/tabular/target_encoding.py
- src/tabular/feature_space.py
- src/tabular/low_count_cat_var_encoding.py
- src/tabular/hierarchical_low_count_var_encoding.py
- src/tabular/merge_ops.py

Design split:

- Row-selection components decide participation and partitioning
- Column-selection components decide engineering, encoding, and projection
- Assembly components perform index-aligned merges

## Feature Selection

Feature selection runs in harmonize_and_project_feature_space on train rows only.

Supported selector modes:

- threshold
- tree_ensemble

Supported tree models:

- gbm
- random_forest
- xgboost (optional dependency)

All selector behavior is configuration-driven through featurizer_config.yaml.

Key kneedle controls:

- FEATURE_SELECTION_TOP_K_MODE
- FEATURE_SELECTION_TOP_K_MIN_RATIO
- FEATURE_SELECTION_MIN_FEATURE_COUNT
- FEATURE_SELECTION_TARGET_FEATURE_COUNT
- FEATURE_SELECTION_REQUIRE_KNEEDLE

## CLI

Initialize a workspace config:

featurization-cli init \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv

Create a provisional starter config:

featurization-cli bootstrap \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv

Use `--overwrite` to replace an existing provisional config file if needed:

featurization-cli bootstrap \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv \
  --overwrite

Run the pipeline:

featurization-cli run --working-dir /path/to/workspace

Run package smoke tests:

pytest -q tests/test_sba_pipeline.py

## How To Extend Safely

1. Put reusable transformations in src/tabular first.
2. Keep workspace stage wrappers thin and explicit.
3. Add new tunables in all three locations:
   - featurizer_config.yaml
   - src/featurization/core/path_coordinator.py
   - src/featurization/core/featurization_init.py
4. Preserve leakage-safe modeling flow:
   - fit artifacts on train only
   - transform val/active with train-fitted artifacts
5. Validate with package tests and workspace integration runs.

## Recommended Read Order

1. documents/sba_pipeline_featurization.md
2. documents/config_blueprint.md
3. documents/path_coordinator_function.md
4. src/featurization/core/sequential_pipeline_runner.py
5. src/tabular/feature_space.py
