import pandas as pd
from tabular.survival_prep import SurvivalDataPreparer


def survival_data_preparation(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Pipeline stage wrapper for survival data preparation."""
    data = context.get("data")
    if data is None:
        raise ValueError("Pipeline context data is required for survival_data_preparation.")

    survival_config = {
        "subject_id_col": stage_cfg.get("subject_id_col", "subject_id"),
        "timestamp_col": stage_cfg.get("timestamp_col", "event_timestamp"),
        "state_col": stage_cfg.get("state_col", "event_state"),
        "terminal_states": stage_cfg.get("terminal_states", []),
        "censored_states": stage_cfg.get("censored_states", []),
        "observation_window": stage_cfg.get("observation_window", {}),
        "static_features": stage_cfg.get("static_features", []),
        "dynamic_aggregation_rules": stage_cfg.get("dynamic_aggregation_rules", {}),
        "duration_unit": stage_cfg.get("duration_unit", None),
    }

    preparer = SurvivalDataPreparer.from_config_dict(survival_config)
    output_df = preparer.transform(data.copy())
    return output_df
