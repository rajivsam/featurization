import os
from typing import Dict, Any

class PathCoordinator:
    """
    Encapsulates structural pipeline layout constants.
    Reconciles config keys with physical directory structures on disk.
    """
    def __init__(self, working_dir: str, config: Dict[str, Any]):
        self.working_dir = os.path.abspath(working_dir)
        self.config = config

    def _remove_anchor_prefix(self, config_value: str, anchor: str) -> str:
        """Removes the anchor prefix from a config value if it's already present."""
        if config_value.startswith(anchor + os.sep):
            return config_value.replace(anchor + os.sep, "", 1)
        return config_value

    @property
    def min_support_threshold(self) -> int:
        """Returns the minimum support threshold for categorical variables."""
        return self.config.get("MIN_SUPPORT_THRESHOLD_CAT_VARS", 5)

    @property
    def structural_type(self) -> str:
        """Returns the dataset structural type (cross-sectional, longitudinal, or panel)."""
        return self.config.get("structural_type", "cross-sectional")

    @property
    def validation_size(self) -> float:
        """Returns validation fraction used for train/validation splitting."""
        return float(self.config.get("VALIDATION_SIZE", 0.2))

    @property
    def feature_selection_min_non_null_rate(self) -> float:
        """Returns minimum non-null rate threshold used for feature selection."""
        return float(self.config.get("FEATURE_SELECTION_MIN_NON_NULL_RATE", 0.01))

    @property
    def feature_selection_method(self) -> str:
        """Returns feature selection strategy: threshold or tree_ensemble."""
        return str(self.config.get("FEATURE_SELECTION_METHOD", "tree_ensemble")).strip().lower()

    @property
    def feature_selection_top_k(self) -> int:
        """Returns top-k cap for selected features (<=0 means keep all)."""
        return int(self.config.get("FEATURE_SELECTION_TOP_K", 50))

    @property
    def feature_selection_top_k_mode(self) -> str:
        """Returns top-k strategy: fixed or kneedle."""
        return str(self.config.get("FEATURE_SELECTION_TOP_K_MODE", "fixed")).strip().lower()

    @property
    def feature_selection_top_k_min(self) -> int:
        """Returns minimum number of features to keep when auto-selecting top-k."""
        return int(self.config.get("FEATURE_SELECTION_TOP_K_MIN", 1))

    @property
    def feature_selection_top_k_min_ratio(self) -> float:
        """Returns minimum fraction of candidate features to retain during auto top-k."""
        return float(self.config.get("FEATURE_SELECTION_TOP_K_MIN_RATIO", 0.0))

    @property
    def feature_selection_min_feature_count(self) -> int:
        """Returns a hard minimum number of features to retain after knee selection."""
        return int(self.config.get("FEATURE_SELECTION_MIN_FEATURE_COUNT", 0))

    @property
    def feature_selection_top_k_max(self) -> int:
        """Returns maximum number of features to keep when auto-selecting top-k (<=0 means no max)."""
        return int(self.config.get("FEATURE_SELECTION_TOP_K_MAX", 0))

    @property
    def feature_selection_target_feature_count(self) -> int:
        """Returns an explicit target feature count override for kneedle mode."""
        return int(self.config.get("FEATURE_SELECTION_TARGET_FEATURE_COUNT", 0))

    @property
    def feature_selection_kneedle_sensitivity(self) -> float:
        """Returns S sensitivity parameter for KneeLocator-based top-k inference."""
        return float(self.config.get("FEATURE_SELECTION_KNEEDLE_SENSITIVITY", 1.0))

    @property
    def feature_selection_kneedle_curve(self) -> str:
        """Returns curve type for KneeLocator (typically convex for descending importances)."""
        return str(self.config.get("FEATURE_SELECTION_KNEEDLE_CURVE", "convex")).strip().lower()

    @property
    def feature_selection_kneedle_direction(self) -> str:
        """Returns direction for KneeLocator (typically decreasing for descending importances)."""
        return str(self.config.get("FEATURE_SELECTION_KNEEDLE_DIRECTION", "decreasing")).strip().lower()

    @property
    def feature_selection_require_kneedle(self) -> bool:
        """Returns whether kneedle mode must fail when KneeLocator is unavailable or unstable."""
        return bool(self.config.get("FEATURE_SELECTION_REQUIRE_KNEEDLE", False))

    @property
    def feature_selection_importance_floor(self) -> float:
        """Returns minimum feature importance required for tree-based selection."""
        return float(self.config.get("FEATURE_SELECTION_IMPORTANCE_FLOOR", 0.0))

    @property
    def feature_selection_tree_model(self) -> str:
        """Returns tree model for feature selection: gbm, random_forest, or xgboost."""
        return str(self.config.get("FEATURE_SELECTION_TREE_MODEL", "gbm")).strip().lower()

    @property
    def feature_selection_tree_n_estimators(self) -> int:
        """Returns number of estimators for tree-based selector."""
        return int(self.config.get("FEATURE_SELECTION_TREE_N_ESTIMATORS", 200))

    @property
    def feature_selection_tree_learning_rate(self) -> float:
        """Returns learning rate for GBM/XGBoost selectors."""
        return float(self.config.get("FEATURE_SELECTION_TREE_LEARNING_RATE", 0.05))

    @property
    def feature_selection_tree_max_depth(self) -> int:
        """Returns max depth for tree-based selector."""
        return int(self.config.get("FEATURE_SELECTION_TREE_MAX_DEPTH", 3))

    @property
    def feature_selection_tree_subsample(self) -> float:
        """Returns subsample ratio for GBM/XGBoost selectors."""
        return float(self.config.get("FEATURE_SELECTION_TREE_SUBSAMPLE", 0.8))

    @property
    def feature_selection_tree_random_state(self) -> int:
        """Returns random state for reproducible tree-based selection."""
        return int(self.config.get("FEATURE_SELECTION_TREE_RANDOM_STATE", 42))

    @property
    def model_ready_numeric_only(self) -> bool:
        """Returns whether model-ready export should contain numeric columns only."""
        return bool(self.config.get("MODEL_READY_NUMERIC_ONLY", True))

    @property
    def metadata_file(self) -> str:
        """Returns the filename for the metadata table."""
        return self.config.get("metadata_file", "sba_loans_metadata_table.csv")

    @property
    def featurization_input_data(self) -> str:
        """Returns the filename for the input data to be featurized."""
        return self.config.get("featurization_input_data", "sba_loans_user_cleaned.csv")

    @property
    def featurized_data_file(self) -> str:
        """Returns the filename for the featurized output data."""
        return self.config.get("featurized_data_file", "featurized_data.csv")

    @property
    def model_ready_data_file(self) -> str:
        """Returns the filename for model-ready post-selection output data."""
        return self.config.get("model_ready_data_file", "model_ready_numeric_data.csv")

    @property
    def metadata_path(self) -> str:
        """Resolves the absolute path to the data dictionary metadata file."""
        target_dir = self.config.get("dd_cleaner_output_dir", "dd_cleaner")
        target_dir = self._remove_anchor_prefix(target_dir, "data")
        filename = self.metadata_file
        abs_dir = os.path.join(self.working_dir, "data", target_dir)
        return os.path.join(abs_dir, filename)

    @property
    def featurization_input_path(self) -> str:
        """Resolves the absolute path to the input data file to be featurized."""
        target_dir = self.config.get("dd_cleaner_output_dir", "dd_cleaner")
        target_dir = self._remove_anchor_prefix(target_dir, "data")
        filename = self.featurization_input_data
        abs_dir = os.path.join(self.working_dir, "data", target_dir)
        return os.path.join(abs_dir, filename)

    @property
    def feature_selection_knee_curve_file(self) -> str:
        """Returns the filename for the feature selection knee curve PNG."""
        return self.config.get("feature_selection_knee_curve_file", "feature_selection_knee_curve.png")

    @property
    def feature_selection_knee_curve_path(self) -> str:
        """Output path for the feature selection knee curve artifact."""
        feat_dir = self.config.get("featurization_output_dir", "featurization")
        feat_dir = self._remove_anchor_prefix(feat_dir, "data")
        filename = self.feature_selection_knee_curve_file
        abs_dir = os.path.join(self.working_dir, "data", feat_dir)
        return os.path.join(abs_dir, filename)

    @property
    def featurized_dataset_path(self) -> str:
        """Output path for the processed featurized CSV."""
        feat_dir = self.config.get("featurization_output_dir", "featurization")
        feat_dir = self._remove_anchor_prefix(feat_dir, "data")
        feat_file = self.featurized_data_file
        abs_dir = os.path.join(self.working_dir, "data", feat_dir)
        return os.path.join(abs_dir, feat_file)

    @property
    def model_ready_dataset_path(self) -> str:
        """Output path for model-ready post-selection numeric dataset."""
        feat_dir = self.config.get("featurization_output_dir", "featurization")
        feat_dir = self._remove_anchor_prefix(feat_dir, "data")
        feat_file = self.model_ready_data_file
        abs_dir = os.path.join(self.working_dir, "data", feat_dir)
        return os.path.join(abs_dir, feat_file)

    @property
    def quarantine_path(self) -> str:
        """Resolves the absolute path to the quarantine directory for failed records."""
        q_dir = self.config.get("quarantine_dir", "featurization/quarantine")
        q_dir = self._remove_anchor_prefix(q_dir, "data")
        abs_dir = os.path.join(self.working_dir, "data", q_dir)
        return abs_dir

    @property
    def featurization_report_path(self) -> str:
        """Output path for the Markdown analytical report (data-level summary)."""
        feat_dir = self.config.get("featurization_output_dir", "featurization")
        feat_dir = self._remove_anchor_prefix(feat_dir, "data")
        report_file = self.config.get("entity_assignment_output", "entity_assignments.md")
        abs_dir = os.path.join(self.working_dir, "data", feat_dir)
        return os.path.join(abs_dir, report_file)

    @property
    def scripts_path(self) -> str:
        """Resolves the absolute path to the user-defined featurization scripts directory."""
        target_dir = self.config.get("script_dir", "featurization_scripts")
        abs_dir = os.path.join(self.working_dir, target_dir)
        return abs_dir

    @property
    def script_logic_path(self) -> str:
        """Resolves the absolute path to the featurization logic script file."""
        filename = self.config.get("script_name", "featurization.py")
        return os.path.join(self.scripts_path, filename)

    def is_stage_configured(self, stage_name: str) -> bool:
        """Checks if a specific stage is present in the pipeline configuration."""
        pipeline = self.config.get("pipeline") or []
        for stage in pipeline:
            if isinstance(stage, dict) and stage.get("name") == stage_name:
                return True
        return False

    @property
    def initialized(self) -> bool:
        """
        Derived state: Returns True if working_dir, metadata filename, 
        and featurization input data filename are all present in the configuration.
        """
        return all([
            self.working_dir is not None,
            bool(self.metadata_file),
            bool(self.featurization_input_data)
        ])