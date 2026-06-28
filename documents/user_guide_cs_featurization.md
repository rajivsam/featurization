# KMDS Featurization User Guide

This user guide explains how to run the regular cross-sectional featurization flow in this repository.
For survival analysis workflows, see `documents/survival_featurization_pipeline.md`.

## 1. What this package does

The package provides a configurable, stage-based featurization pipeline.
It is designed to:

- read cleaned input data from a workspace config anchor
- execute ordered stage wrappers in `featurization_scripts/featurization.py`
- accumulate engineered features horizontally by index
- preserve leakage-safe modeling behavior through train/val/active partitioning
- write a consolidated `featurized_data.csv` and a `model_ready_numeric_data.csv`

## 2. Core workflow

1. `featurization-cli init` or `bootstrap` creates workspace config anchors.
2. `featurization_scripts/featurization.py` implements stage wrappers.
3. `featurization-cli run` executes the pipeline via `src/featurization/core/sequential_pipeline_runner.py`.
4. Each stage returns a `pd.DataFrame` aligned to the current survivor universe index.
5. The runner concatenates stage outputs horizontally and persists final artifacts.

## 3. Configuration

The main workspace config file is `featurizer_config.yaml`.
It contains:

- input anchors such as `metadata_file` and `featurization_input_data`
- output anchors such as `featurized_data_file` and `model_ready_data_file`
- pipeline stage definitions under `pipeline`
- model selection and feature-selection controls

All file anchors are resolved relative to the `working_dir` configured in `featurizer_config.yaml`. The actual absolute filesystem paths will differ between users and installations.

A stage definition looks like this:

```yaml
pipeline:
  - name: Example Stage
    method: example_stage
    entity: System
    sub_filter: Example
```

The pipeline stage contract is:

```python
def example_stage(context: dict, stage_cfg: dict) -> pd.DataFrame:
    ...
```

## 4. Regular cross-sectional featurization

Regular cross-sectional featurization assumes an input dataset that already has one row per record.
It does not perform survival timeline flattening.

Typical stages include:

- `record_id_definition` — creates or promotes a stable `record_id` index
- `prepare_categorical_data` — selects and prepares categorical features
- `prepare_numerical_data` — selects and prepares numerical features
- `low_count_featurization_of_cat_vars` — groups rare categories and recodes low-support levels
- `hierarchical_low_count_var_encoding` — applies hierarchical recoding for structured categorical values like NAICS
- `loan_status_recoding` — maps business status labels into modeling labels
- `filter_modeling_universe` — drops non-modeled rows, such as active holdout records
- `stratified_train_val_split` — creates a train/val split
- `target_encode_categorical_vars` — fits target encoding on train only and transforms remaining rows
- `harmonize_and_project_feature_space` — selects feature schema and projects modeled + active partitions
- `merge_modeled_and_active_partitions` — reconciles modeled and active rows into one final dataset

## 5. What to edit for a new dataset

1. Update `featurizer_config.yaml` anchors for your workspace paths.
2. Add or modify pipeline stage entries under `pipeline`.
3. Implement or reuse stage wrappers in `featurization_scripts/featurization.py`.
4. Add reusable transformation logic in `src/tabular/` when it should be shared across datasets.
5. Run `featurization-cli run --working-dir /path/to/workspace` to execute.

## 6. Validation

Run package tests for core behavior:

```bash
pytest -q tests/test_sba_pipeline.py tests/test_survival_prep.py tests/test_survival_featurizer_pipeline.py
```

If you add a new stage or change configuration handling, include a test covering the new behavior.

## 7. Agent-assisted featurization

After you confirm your workspace setup and stage logic, you can use an agent like this one to execute and validate the featurization pipeline.

The agent should initialize on the following documents before working on the pipeline:

- `documents/stash.md`
- `documents/sba_pipeline_featurization.md`
- `documents/survival_featurization_pipeline.md`

The first two documents provide the package runtime model, stage contract, and SBA pipeline conventions. The survival document provides the detailed configuration and wiring for event-log or interval-long survival workloads.

## 8. Survival analysis note

If your dataset is an event log, interval log, or needs one-row-per-subject survival flattening, use the survival guide instead:

- `documents/survival_featurization_pipeline.md`

The survival guide explains the additional preparer, configuration keys, and pipeline wiring for survival analysis workloads.
