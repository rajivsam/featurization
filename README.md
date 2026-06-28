# KMDS Featurization

KMDS Featurization turns cleaned data into model-ready datasets using a configurable stage pipeline.

It is designed to be flexible:
- works with standard cross-sectional datasets
- supports survival analysis workflows when needed
- keeps feature engineering and train/validation flow leakage-safe
- resolves file anchors relative to the workspace `working_dir`

## What it produces

The main outputs are:
- `featurized_data.csv`: a consolidated engineered dataset
- `model_ready_numeric_data.csv`: a numeric model-ready export for modeling

This tool also creates diagnostic artifacts such as:
- `feature_selection_knee_curve.png`

## How it works

The pipeline is built from stage wrappers in `featurization_scripts/featurization.py`. Each stage returns a DataFrame and the runner concatenates stage outputs by index.

Key ideas:
- every row can be assigned a stable `record_id`
- stages are configured in `featurizer_config.yaml`
- stage output is merged horizontally to build the final dataset
- only the final stage may intentionally add new records back into the pipeline

## Survival vs. regular featurization

This repository supports two kinds of workflows:

- regular cross-sectional featurization: one row per input record
- survival featurization: one row per subject after flattening event or interval history

If you are doing survival analysis, read:
- `documents/survival_featurization_pipeline.md`

For regular workflows, see:
- `documents/user_guide_cs_featurization.md`

## Quick start

Initialize a workspace config:

```bash
featurization-cli init \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv
```

Create a provisional starter config:

```bash
featurization-cli bootstrap \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv
```

Run the pipeline:

```bash
featurization-cli run --working-dir /path/to/workspace
```

If you want to validate survival config first, check:
- `documents/survival_featurization_pipeline.md`

## Testing

Run the core tests with:

```bash
pytest -q tests/test_sba_pipeline.py tests/test_survival_prep.py tests/test_survival_featurizer_pipeline.py
```

## Notes for users

- `featurizer_config.yaml` file anchors are workspace-relative.
- absolute paths depend on your local `working_dir` setting.
- stage wrappers should stay thin and use shared `src/tabular/` logic.
- survival support is a use-case extension, not a universal default.

## Recommended documents

- `documents/sba_pipeline_featurization.md`
- `documents/config_blueprint.md`
- `documents/path_coordinator_function.md`
- `documents/user_guide_cs_featurization.md`
- `documents/survival_featurization_pipeline.md`
