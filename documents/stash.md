# Featurization Stash: Copilot Initialization Baseline

Use this document as the first-read initialization context for coding sessions.

## Session Start Checklist
1. Read this file first, then read active docs listed in Canonical Context.
2. Confirm current pair of baseline commits (refresh before release commit if this stash changed).
3. Confirm stage contract remains method(context, stage_cfg) -> DataFrame.
4. Confirm active categorical suffix is _rcs.
5. Confirm current input data anchor is data/dd_cleaner/sba_loans_user_cleaned.csv.
6. Run package test smoke checks:
    - tests/test_sba_pipeline.py
    - tests/test_low_count_cat_var_encoding.py
    - tests/test_feature_space.py
7. Route new changes using the Two-Repo Workflow rules below before committing.

## Canonical Context
- Active architecture docs:
    - documents/sba_pipeline_featurization.md
    - documents/path_coordinator_function.md
    - documents/config_blueprint.md
- Legacy/stale docs were moved to documents/discarded and should not drive implementation.

## Core Runtime Model
- Pipeline model: index-centric waterfall.
- Universal anchor: record_id index.
- Stage contract: method(context, stage_cfg) -> DataFrame.
- Stage purity: stages return result DataFrames; source CSV files are never modified.
- Waterfall behavior: runner updates survivor universe to returned index after each stage.
- Join behavior: runner concatenates stage outputs horizontally by index.

## Authoritative Paths
- Repo config file: featurizer_config.yaml.
- Workspace `working_dir`: configured in `featurizer_config.yaml`; the actual absolute path varies by installation.
- Input data file: `data/dd_cleaner/sba_loans_user_cleaned.csv` relative to the workspace `working_dir`.
- Metadata file: `data/dd_cleaner/sba_loans_metadata_table.csv` relative to the workspace `working_dir`.
- User logic script: `featurization_scripts/featurization.py` relative to the workspace `working_dir`.

## Current Stage Inventory
1. record_id_definition
2. borrower_geo_coding
3. prepare_categorical_data
4. prepare_numerical_data
5. merge_categorical_and_numerical
6. merge_with_borrower_geo
7. low_count_featurization_of_cat_vars
8. hierarchical_low_count_var_encoding
9. loan_status_recoding
10. filter_modeling_universe
11. stratified_train_val_split
12. target_encode_categorical_vars
13. harmonize_and_project_feature_space
14. merge_modeled_and_active_partitions

## Current Stage Semantics
- record_id_definition:
    - Creates record_id if missing and returns it for index promotion.
- borrower_geo_coding:
    - Fallback chain is ZIP -> CITY -> STATE centroid.
    - Geo attributes sourced from metadata tag is_geographic with sub-filter Borrower.
    - Returns borrower_latitude and borrower_longitude.
- prepare_categorical_data:
    - Builds categorical payload without row filtering.
- prepare_numerical_data:
    - Builds numerical payload without row filtering.
- merge_categorical_and_numerical:
    - Index-based tabular merge for categorical + numerical payloads.
- merge_with_borrower_geo:
    - Index-based tabular merge for structured payload + borrower geo.
- low_count_featurization_of_cat_vars:
    - Two-pass logic: roll rare levels to OTHERS, then enforce support sequentially.
    - Rows with insufficient OTHERS support are dropped immediately in-stage.
    - Output categorical suffix is _rcs (recoded for support).
- hierarchical_low_count_var_encoding:
    - NAICS-focused hierarchical low-support recoding via right-side masking.
    - Output column is naicscode_rcs.
- loan_status_recoding:
    - Maps statuses to {-1, 0, 1}.
    - Uses expanded matching for active/closed/distressed operational labels.
    - Raises on truly unknown labels to protect integrity.
- filter_modeling_universe:
    - Drops active class (-1) from modeling survivors.
    - Preserves active rows in context for downstream scoring/reconciliation.
- stratified_train_val_split:
    - Adds dataset_split train/val using VALIDATION_SIZE.
- target_encode_categorical_vars:
    - Fits TargetEncoder on train only.
    - Transforms modeling and active holdout with same train-fitted encoder.
    - Enforces explicit exclusion policy from stage config.
    - Reuses borrower geographic subset drop-list to block geo source columns.
    - Encodes only rarity-corrected categorical variants when both raw and _rcs exist.
- harmonize_and_project_feature_space:
    - Selects canonical features on train using configured method:
        - threshold mode, or
        - tree_ensemble mode (gbm/random_forest/xgboost).
    - Supports fixed or kneedle feature-count selection.
    - Supports explicit FEATURE_SELECTION_TARGET_FEATURE_COUNT override.
    - Emits feature-selection summary and knee-curve PNG artifact.
    - Projects modeled and active data into one aligned schema.
- merge_modeled_and_active_partitions:
    - Merges projected modeled and active partitions into one output dataset.

## Guardrails
- Do not hardcode filesystem paths inside stage logic; use context-resolved inputs.
- Do not mutate source data files.
- Prefer real dataset validation over mocked data.
- Keep stage outputs index-aligned with current survivor universe.
- Only final merge stage may intentionally re-introduce indices (active partition), via allow_new_indices.
- Persisted CSV outputs must be written with index=False (no record_id/Unnamed index artifact columns).

## Validation Baseline
- test files:
    - tests/test_sba_pipeline.py
    - tests/test_merge_ops.py
    - tests/test_feature_space.py
    - tests/test_low_count_cat_var_encoding.py
- latest status: passing for merge package component + hybrid pipeline + tree-based selection wiring + categorical OR tagging + kneedle controls.

## Next Implementation Boundary
- Current session endpoint: produce model_ready_numeric_data.csv from full pipeline run.
- Current feature selection mode: config-driven threshold or tree_ensemble with kneedle controls.
- Tree selector + kneedle parameters are wired through:
    - featurizer_config.yaml
    - src/featurization/core/path_coordinator.py
    - src/featurization/core/featurization_init.py

## Two-Repo Workflow (Package + Workspace)
- Purpose:
    - Keep framework evolution isolated in the featurization package repo.
    - Keep real-data stage logic and integration outputs in the SBA workspace repo.

- Repo roles:
    - Package repo (/home/rajiv/programming/featurization):
        - Owns runner/core interfaces, path coordination, package tests, and docs/stash.
    - Workspace repo (/home/rajiv/programming/kmds_migration/sba_migration):
        - Owns featurization_scripts/featurization.py, real data config, and end-to-end integration runs.

- Change routing rule:
    - If change affects orchestration/contracts: commit in package repo.
    - If change affects domain stage behavior for SBA: commit in workspace repo.
    - If change affects both: make two commits, one per repo, and reference the paired hash in commit messages.

- Baseline pairing for this state:
    - Package baseline commit: d7c487d
    - Workspace baseline commit: 4ef0bc5

- Recommended dev loop:
    1. Modify package code in featurization repo.
    2. Run package tests there.
    3. Validate integrated behavior from SBA workspace using real data and featurizer_config.yaml.
    4. Commit package changes first, workspace changes second.
    5. Record both hashes in this stash when contract-level behavior changes.

- Future testing direction:
    - Create a dedicated integration-test workspace cloned from SBA migration when package API stabilizes.
    - Keep synthetic/unit tests in package repo; keep real-data integration tests in workspace clone.

## Session Sign-Off (2026-06-10)
- Completed in package repo:
    - Added strict leakage safeguards and configurable exclusion patterns across categorical encoding and feature selection.
    - Added kneedle-based feature-count controls with strict-mode behavior and explicit target override.
    - Added knee-curve plotting support and dependency plumbing.
    - Updated CSV persistence to index=False for featurized and model-ready outputs.
    - Updated categorical tagging to OR logic: logical_type=categorical OR pandas categorical-compatible dtype.
    - Added/updated tests:
        - tests/test_merge_ops.py
        - tests/test_feature_space.py
        - tests/test_low_count_cat_var_encoding.py
- Validation run:
    - pytest -q tests/test_feature_space.py tests/test_low_count_cat_var_encoding.py tests/test_merge_ops.py tests/test_sba_pipeline.py
    - Result: passing.
- Repo state:
    - Package repo has coordinated updates across core, tabular modules, configs, docs, and tests.
    - SBA workspace wrapper/config updated for explicit leakage controls and runtime diagnostics.

Last updated: 2026-06-10