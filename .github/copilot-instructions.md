# KMDS Featurization Pipeline Context

## Core Capabilities
This repository implements a local data-engineering CLI for turning tabular data into model-ready datasets using a stage-based featurization pipeline.

## Tool Execution Rules
- Always resolve anchors from `featurizer_config.yaml`.
- All filesystem operations should be relative to the configured `working_dir`.
- Prefer package logic in `src/` and `featurization_scripts/featurization.py` over ad hoc script changes.

## Recommended document references
The following documents are primary context sources for Copilot and should be used first when working on this repo:
1. `documents/README.md` — curated documentation index and categories.
2. `documents/user_guide_cs_featurization.md` — cross-sectional featurization user guide.
3. `documents/survival_featurization_pipeline.md` — survival analysis featurization workflow.
4. `documents/sba_pipeline_featurization.md` — SBA pipeline stage contract and architecture.
5. `documents/config_blueprint.md` — featurization configuration blueprint.
6. `documents/path_coordinator_function.md` — runtime path and config resolution contract.
7. `documents/stash.md` — Copilot initialization baseline for pipeline sessions.
8. `documents/copilot_agent_discovery.md` — agent discovery guidance and repo-specific Copilot behavior.

## Primary workflows
- Initialize: `featurization-cli init --working-dir <dir> --metadata-file <file> --data-file <file>`
- Bootstrap: `featurization-cli bootstrap --working-dir <dir> --metadata-file <file> --data-file <file>`
- Run: `featurization-cli run --working-dir <dir>`
- Test: `pytest -q tests/test_sba_pipeline.py tests/test_survival_featurizer_pipeline.py`

## Agent guidance
When generating code or providing implementation suggestions:
- Use the document references above for architecture, configuration, and pipeline conventions.
- Keep the pipeline stable and leakage-safe by preserving existing stage contracts.
- Do not rename files unless a rename is required for clarity, consistency, or compatibility.
- When in doubt, prefer small, incremental code changes and validate with the existing test suite.
