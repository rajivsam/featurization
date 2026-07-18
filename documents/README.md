# Documentation Directory

This directory contains the core package documentation for `kmds-featurization`.

## Purpose

These files are curated to support both human contributors and AI-assisted development by grouping the most important architecture, configuration, and usage guides in one place.

## How to use this directory

- `datapackage.json` provides a metadata index for the documented resources.
- `README.md` provides a categorized overview of the available documents.
- `.github/copilot-instructions.md` can reference the most important top-level docs when guiding Copilot.

## Document categories

### Core pipeline and onboarding

- `stash.md` — Copilot initialization baseline and first-read context.
- `client_onboarding.md` — package consumer onboarding for workspace setup and orchestration.
- `user_guide_cs_featurization.md` — cross-sectional featurization user guide.
- `sba_pipeline_featurization.md` — SBA pipeline stage and contract specification.

### Configuration and runtime wiring

- `config_blueprint.md` — `featurizer_config.yaml` configuration blueprint.
- `path_coordinator_function.md` — PathCoordinator routing and config contract.
- `feature_advisor_service.md` — feature advisor service design and dataset archetypes.
- `notebook_utils_usage.md` — notebook examples for retrieving artifacts using `working_dir`.

### Model and encoding design

- `categorical_var_encoder_guidelines.md` — categorical encoding architecture and best practices.
- `encoding_non_numerical_attrib.md` — non-numerical attribute encoding recommendations.
- `text_attribute_featurization.md` — text feature engineering best practices.

### Survival analysis and testing

- `survival_featurization_pipeline.md` — survival analysis featurization workflow wiring.
- `survival_pipeline_prompt.md` — survival pipeline prompt guidance.
- `testing_survival_featurization_pipeline.md` — survival pipeline test case examples.
- `test_documentation_principles.md` — KMDS testing and documentation principles.

### Meta and project context

- `consolidated_featurization_design.md` — consolidated architecture and service design.
- `copilot_agent_discovery.md` — Copilot discovery and context-aware agent guidance.

## Notes

This directory is intended to be a curated context source for both contributors and AI agents. Keep filenames descriptive and stable unless a rename is needed for clarity or compatibility.
