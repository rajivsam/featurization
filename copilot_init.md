# Copilot Initialization Prompt

Copy/paste this at the start of a new session:

Please initialize from documents/stash.md first, then read documents/sba_pipeline_featurization.md.
Treat documents/stash.md as the authoritative bootstrap context.
Do not use any docs under documents/discarded.

Confirm before coding:

1. Current pipeline stage inventory
2. Stage contract: method(context, stage_cfg) -> DataFrame
3. Two-repo workflow (package repo vs SBA workspace repo)

Execution requirements:

1. Keep stage wrappers in featurization_scripts/featurization.py thin and readable.
2. Put reusable logic in src/tabular modules.
3. Preserve leakage-safe modeling flow:
   - fit artifacts on train only
   - transform val/active with train-fitted artifacts
4. Keep configuration-driven behavior in featurizer_config.yaml with counterparts in:
   - src/featurization/core/featurization_init.py
   - src/featurization/core/path_coordinator.py
5. Keep active reconciliation aligned to modeled feature space before merge.
6. Preserve generation of:
   - consolidated output file
   - model_ready_numeric_data.csv

When done, run tests and report:

1. What changed
2. Validation results
3. Any follow-up risks or next-step recommendations
