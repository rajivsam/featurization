# KMDS Featurization Package Interface

This package provides the KMDS featurization framework for turning cleaned dataset inputs into model-ready feature datasets. It is focused on pipeline orchestration, stage contract consistency, leakage-safe modeling flow, and metadata-driven feature advice.

## What this package supports

- Cross-sectional datasets with categorical and numerical feature assembly.
- Temporal / event-log datasets used in survival and risk modeling.
- Panel and longitudinal datasets through the structural type configuration.
- Wide-and-short datasets as a supported structural type, with special guidance for feature selection.
- Cleaned input data from `dd-parser-cleaner`, not raw dirty source files.

## Core design principles

- **Stage contract:** every stage implements `method(context, stage_cfg) -> DataFrame`.
- **Index-centric waterfall:** `record_id` is the universal anchor and each stage returns rows aligned to the current survivor universe.
- **Immutable source data:** source CSV files are never modified by stage logic.
- **Config-driven behavior:** all runtime action is driven from `featurizer_config.yaml` and `PathCoordinator` resolves paths.
- **Leakage-safe flow:** fit artifacts only on train data, transform validation and active rows using train-fitted artifacts.
- **Thin workspace wrappers:** `featurization_scripts/featurization.py` contains stage wrappers, while reusable logic lives in `src/tabular`.
- **Aligned output schema:** the final merge stage projects modeled and active partitions into one aligned dataset and produces a numeric-only model-ready export.

## Supported dataset types

This package is configured to support:

- `cross-sectional`
- `longitudinal`
- `panel`
- `temporal` / event-log
- `wide and short`

The package is most mature for cross-sectional and event-log workflows, with explicit guidance for wide-and-short data and survival-oriented pipelines.

## Client onboarding

Clients should onboard by:

1. Creating a workspace directory.
2. Ensuring `featurizer_config.yaml` is present in the workspace root.
3. Pointing `working_dir` to the workspace root or absolute data root.
4. Providing a cleaned input file and metadata authority table from `dd-parser-cleaner`.
5. Running the CLI commands below to initialize, bootstrap, and validate.

### Primary onboarding documents

- `documents/user_guide_cs_featurization.md` — cross-sectional usage and config examples.
- `documents/survival_featurization_pipeline.md` — event-log and survival pipeline guidance.
- `documents/path_coordinator_function.md` — path resolution and workspace layout.
- `documents/config_blueprint.md` — configuration anchors and field definitions.
- `documents/consolidated_featurization_design.md` — architecture and output semantics.
- `documents/feature_advisor_service.md` — how the advisor works and how it uses metadata.
- `documents/notebook_utils_usage.md` — notebook-based workspace discovery and artifact loading.
- `documents/sba_pipeline_featurization.md` — current SBA pipeline inventory and stage semantics.
- `documents/stash.md` — authoritative bootstrap context and guardrails.

## CLI interface

This package exposes the following CLI entry point:

- `featurization-cli init` — initialize a featurization workspace config.
- `featurization-cli bootstrap` — generate a provisional starter configuration.
- `featurization-cli run` — execute the configured featurization pipeline.
- `featurization-cli advise` — generate feature-advisor recommendations from metadata.
- `featurization-cli check` — verify if a named pipeline stage is configured.
- `featurization-cli add-stage` — add a custom metadata-based stage to the pipeline.

## Python interface

The package exports these Python interfaces:

- `from featurization import get_package_info`
- `from featurization import load_package_agents_documentation`
- `from featurization import get_cli_command_names`
- `from featurization import FeatureAdvisorUtil, FeatureAdvisorPromptConfig`

### Runtime discovery

- `get_package_info()` returns package metadata, CLI commands, documentation pointers, and guidance.
- `load_package_agents_documentation()` returns the contents of `AGENTS.md` from the installed package.

### Feature advisor service

- Use `FeatureAdvisorUtil` and `FeatureAdvisorPromptConfig` to generate recommendations from dataset metadata.
- The advisor prefers native categorical handling for CatBoost, XGBoost, and LightGBM.
- When explicit encoding is needed, the advisor recommends low-count and hierarchical encoding strategies.
- Prompt templates are packaged under `src/featurization/prompts/feature_advisor_prompt.yaml`.

## Featurization inputs and metadata

The package expects:

- A cleaned dataset input file specified in `featurizer_config.yaml` under `featurization_input_data`.
- A metadata table specified under `metadata_file`.
- A `dd_cleaner_output_dir` where `dd-parser-cleaner` places `user_cleaned_output_filename` and metadata artifacts.

### dd-parser-cleaner notebook interface

Clients may use the `dd-parser-cleaner` notebook interface to inspect dataset metadata and confirm inputs before featurization.

- The package provides notebook helpers in `src/featurization/notebook_utils.py`.
- These helpers resolve workspace paths and load metadata and cleaned input datasets.
- Example notebook usage is provided in `notebooks/notebook_utils_cleaning_stage.ipynb`.

## Featurization outputs

The package produces:

- Consolidated `featurized_data.csv` with engineered features and dataset markers.
- `model_ready_numeric_data.csv` containing numeric-only feature data for model training.
- Optional feature-selection knee curve artifacts for cross-sectional workflows.
- Feature advisor recommendation artifacts under the configured `featurization_output_dir`.

## Design and package boundaries

- Stage logic is implemented in `src/tabular` and should be reusable.
- Workspace-specific wrappers remain in `featurization_scripts/featurization.py`.
- The package does not own raw data cleaning; it consumes cleaned input produced by `dd-parser-cleaner`.
- The package does not mutate original data files.

## Package data exposure

- `AGENTS.md` is packaged as a package resource and can be loaded at runtime.
- Use `load_package_agents_documentation()` to read this file from an installed environment.
- Clients can also consult `get_package_info()` for the package resource pointer.

## Recommended client workflow

1. Bootstrap or initialize the workspace config.
2. Confirm `working_dir`, `metadata_file`, `featurization_input_data`, and `dd_cleaner_output_dir`.
3. Use the notebook helpers if desired to preview metadata authority and cleaned dataset paths.
4. Run `featurization-cli run --working-dir <workspace>`.
5. Use `featurization-cli advise --working-dir <workspace> --model-intent <intent>` to obtain encoding guidance.
6. Review outputs in `data/featurization` and confirm `model_ready_numeric_data.csv`.

## Notes for package clients

- This package is a KMDS featurization orchestration layer, not a general-purpose data cleaner.
- It is best used alongside `dd-parser-cleaner` to provide the authoritative cleaned dataset and metadata inputs.
- For dataset-specific implementation details, clients should read the documents in the `documents/` directory.
