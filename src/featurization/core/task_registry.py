"""Task-aware pipeline registry for featurization workflows.

This module defines the supported task families and the default behavior each task
expects from the pipeline. The goal is to keep the stage contract generic while
making the target semantics explicit at configuration time.
"""

VALID_TASK_TYPES = {
    "classification": {
        "classification",
        "classif",
        "binary_classification",
        "multiclass_classification",
        "binary classification",
        "multi class classification",
    },
    "regression": {
        "regression",
        "continuous_target",
        "continuous target",
        "continuous-regression",
    },
    "time_to_event": {
        "time_to_event",
        "time-to-event",
        "time to event",
        "survival",
        "survival_analysis",
        "survival analysis",
    },
    "clustering": {
        "clustering",
        "cluster",
        "unsupervised",
        "unsupervised_clustering",
    },
}

_TASK_ALIASES = {}
for canonical, aliases in VALID_TASK_TYPES.items():
    for alias in aliases:
        _TASK_ALIASES[alias.strip().lower().replace("-", "_").replace(" ", "_")] = canonical


def normalize_task_type(value: str | None) -> str:
    """Normalize a task type value to a canonical package task identifier."""
    if value is None:
        return "classification"

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in _TASK_ALIASES:
        return _TASK_ALIASES[normalized]

    allowed_values = ", ".join(sorted(VALID_TASK_TYPES.keys()))
    raise ValueError(
        f"Unsupported task_type '{value}'. Supported task types: {allowed_values}."
    )


def get_task_defaults(task_type: str | None) -> dict:
    """Return default pipeline semantics for a supported task type."""
    canonical = normalize_task_type(task_type)

    defaults = {
        "classification": {
            "split_strategy": "stratified",
            "target_kind": "label",
            "feature_selection": "tree_ensemble",
            "requires_supervised_target": True,
            "supports_rare_category_encoding": True,
        },
        "regression": {
            "split_strategy": "random",
            "target_kind": "continuous",
            "feature_selection": "tree_ensemble_regression",
            "requires_supervised_target": True,
            "supports_rare_category_encoding": True,
        },
        "time_to_event": {
            "split_strategy": "time_aware",
            "target_kind": "duration_event",
            "feature_selection": "survival_aware",
            "requires_supervised_target": True,
            "supports_rare_category_encoding": True,
        },
        "clustering": {
            "split_strategy": "none",
            "target_kind": "unsupervised",
            "feature_selection": "variance",
            "requires_supervised_target": False,
            "supports_rare_category_encoding": False,
        },
    }

    runtime = dict(defaults[canonical])
    runtime["task_type"] = canonical
    return runtime


def get_task_runtime_config(task_type: str | None) -> dict:
    """Return the canonical runtime configuration for a task family."""
    return get_task_defaults(task_type)


def get_default_pipeline(task_type: str | None) -> list[dict]:
    """Return a starter pipeline template for the requested task type.

    These entries are intentionally lightweight skeletons that users can customize in
    their workspace featurization script. The goal is to provide task-aware defaults
    without hard-wiring a single modeling objective into repository code.
    """
    canonical = normalize_task_type(task_type)

    base_stages = [
        {"name": "Record ID Generation", "method": "record_id_definition", "entity": "System", "sub_filter": "System"},
        {"name": "Prepare Categorical Data", "method": "prepare_categorical_data", "entity": "categorical", "sub_filter": "modeling"},
        {"name": "Prepare Numerical Data", "method": "prepare_numerical_data", "entity": "numerical", "sub_filter": "modeling"},
        {"name": "Merge Categorical And Numerical", "method": "merge_categorical_and_numerical", "entity": "System", "sub_filter": "merge"},
        {"name": "Low Count Categorical Encoding", "method": "low_count_featurization_of_cat_vars", "entity": "categorical", "sub_filter": "low_count"},
    ]

    if canonical == "classification":
        return [{
            "name": "Example Feature Stage",
            "method": "example_feature_stage",
            "entity": "System",
            "sub_filter": "example",
            "allow_new_indices": False,
        }]

    if canonical == "regression":
        return [{
            "name": "Example Feature Stage",
            "method": "example_feature_stage",
            "entity": "System",
            "sub_filter": "example",
            "allow_new_indices": False,
        }]

    if canonical == "time_to_event":
        return [{
            "name": "Example Feature Stage",
            "method": "example_feature_stage",
            "entity": "System",
            "sub_filter": "example",
            "allow_new_indices": False,
        }]

    return [{
        "name": "Example Feature Stage",
        "method": "example_feature_stage",
        "entity": "System",
        "sub_filter": "example",
        "allow_new_indices": False,
    }]
