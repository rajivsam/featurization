# KMDS Featurization Pipeline Context

## Core Capabilities
This repo is a local data-engineering CLI for turning tabular data into model-ready datasets using a horizontal-merge architecture.

## Tool Execution Rules
- Always refer to `featurizer_config.yaml` for data paths.
- All operations must be relative to the `working_dir`.

## Required File Context Mapping
When handling pipeline tasks, instruct Copilot to read:
1. Cross-Sectional Data: `documents/user_guide_cs_featurization.md`
2. Survival Analysis: `documents/survival_featurization_pipeline.md`
3. Logic: `src/` and `featurization_scripts/featurization.py`

## CLI Commands
- Initialize: `featurization-cli init --working-dir <dir> --metadata-file <file> --data-file <file>`
- Bootstrap: `featurization-cli bootstrap --working-dir <dir> --metadata-file <file> --data-file <file>`
- Run: `featurization-cli run --working-dir <dir>`
- Test: `pytest -q tests/test_sba_pipeline.py`
