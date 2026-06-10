# Featurization Stash: Copilot Initialization Baseline

Use this document as the first-read initialization context for coding sessions.

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
- Working directory anchor: /home/rajiv/programming/dd_parser_cleaner_migration/sba_migration.
- Input data file: data/dd_cleaner/sba_loans_user_cleaned.csv.
- Metadata file: data/dd_cleaner/sba_loans_metadata_table.csv.
- User logic script: featurization_scripts/featurization.py.

## Current Stage Inventory
1. record_id_definition
2. borrower_geo_coding
3. low_count_featurization_of_cat_vars
4. loan_status_recoding

## Current Stage Semantics
- record_id_definition:
    - Creates record_id if missing and returns it for index promotion.
- borrower_geo_coding:
    - Fallback chain is ZIP -> CITY -> STATE centroid.
    - Returns borrower_latitude and borrower_longitude.
- low_count_featurization_of_cat_vars:
    - Two-pass logic: roll rare levels to OTHERS, then enforce support sequentially.
    - Rows with insufficient OTHERS support are dropped immediately in-stage.
    - Output categorical suffix is _rcs (recoded for support).
- loan_status_recoding:
    - Maps statuses to {-1, 0, 1}.
    - Uses expanded matching for active/closed/distressed operational labels.
    - Raises on truly unknown labels to protect integrity.

## Guardrails
- Do not hardcode filesystem paths inside stage logic; use context-resolved inputs.
- Do not mutate source data files.
- Prefer real dataset validation over mocked data.
- Keep stage outputs index-aligned with current survivor universe.

## Validation Baseline
- test file: tests/test_sba_pipeline.py
- latest status: passing after _rcs suffix update and status mapping stabilization.

Last updated: 2026-06-10