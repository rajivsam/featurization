# Featurization PathCoordinator: Routing And Config Contract

PathCoordinator centralizes all path and runtime-parameter resolution used by the pipeline.

## 1. Why It Exists

Without a coordinator, stage logic tends to accumulate hidden assumptions:
- hardcoded directories
- ad-hoc filenames
- duplicated constant defaults

PathCoordinator prevents that by making config-driven values available as typed properties.

## 2. What It Resolves

Path properties:
- metadata_path
- featurization_input_path
- featurized_dataset_path
- model_ready_dataset_path
- quarantine_path
- script_logic_path

Runtime/modeling properties:
- min_support_threshold
- validation_size
- feature_selection_min_non_null_rate
- model_ready_numeric_only

Tree selector properties:
- feature_selection_method
- feature_selection_top_k
- feature_selection_importance_floor
- feature_selection_tree_model
- feature_selection_tree_n_estimators
- feature_selection_tree_learning_rate
- feature_selection_tree_max_depth
- feature_selection_tree_subsample
- feature_selection_tree_random_state

## 3. How It Is Used

Flow at runtime:
1. PipelineRunner loads config.
2. PipelineRunner creates PathCoordinator(working_dir, config).
3. Data loader reads source data and metadata using resolved paths.
4. Stage logic accesses config behavior through resolver-backed values in context.

This keeps stage methods simple and avoids path/config plumbing inside transformation code.

## 4. Design Rule For New Parameters

When adding a new tuneable:
1. Add key to featurizer_config.yaml.
2. Add typed property in PathCoordinator.
3. Add default in initialize_config (featurization_init.py).
4. Read the parameter via resolver in stage logic.

Following this rule keeps behavior reproducible and discoverable for new engineers.

## 5. Relationship To The Hybrid Pipeline

The current hybrid flow has a front feature-assembly section and a leakage-safe modeling section.
PathCoordinator supports both by resolving:
- shared input/output paths
- model-selection constants for train-only tree-based feature selection
- output routing for final consolidated and model-ready artifacts
