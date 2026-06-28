import pandas as pd
import pytest

from tabular.survival_prep import SurvivalDataPreparer


def _build_survival_config(**overrides):
    base = {
        "subject_id_col": "subject_id",
        "timestamp_col": "timestamp",
        "state_col": "state",
        "terminal_states": ["Resolved", "Closed"],
        "censored_states": [],
        "observation_window": {
            "start_mode": "subject_first",
            "fixed_start_date": None,
            "end_mode": "dataset_max",
            "fixed_end_date": None,
        },
        "static_features": [],
        "dynamic_aggregation_rules": {},
        "duration_unit": "days",
    }
    base.update(overrides)
    return base


def test_raw_event_log_terminal_events_are_transformed_correctly():
    df = pd.DataFrame([
        {"incident_id": "INC101", "timestamp": "2026-01-01 09:00:00", "state": "New", "priority": "High"},
        {"incident_id": "INC101", "timestamp": "2026-01-03 14:00:00", "state": "Active", "priority": "High"},
        {"incident_id": "INC101", "timestamp": "2026-01-05 09:00:00", "state": "Closed", "priority": "High"},
        {"incident_id": "INC102", "timestamp": "2026-01-02 10:00:00", "state": "New", "priority": "Critical"},
        {"incident_id": "INC102", "timestamp": "2026-01-03 10:00:00", "state": "Resolved", "priority": "Critical"},
        {"incident_id": "INC103", "timestamp": "2026-01-08 12:00:00", "state": "Closed", "priority": "Low"},
        {"incident_id": "INC103", "timestamp": "2026-01-02 12:00:00", "state": "New", "priority": "Low"},
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    config = _build_survival_config(
        subject_id_col="incident_id",
        static_features=["priority"],
        dynamic_aggregation_rules={"priority": "first"},
    )

    preparer = SurvivalDataPreparer.from_config_dict(config)
    result = preparer.transform(df)

    assert set(result.columns) >= {"incident_id", "survival_duration", "survival_event", "priority"}
    assert result.loc[result["incident_id"] == "INC101", "survival_duration"].iloc[0] == pytest.approx(4.0)
    assert result.loc[result["incident_id"] == "INC101", "survival_event"].iloc[0] == 1
    assert result.loc[result["incident_id"] == "INC102", "survival_duration"].iloc[0] == pytest.approx(1.0)
    assert result.loc[result["incident_id"] == "INC102", "survival_event"].iloc[0] == 1
    assert result.loc[result["incident_id"] == "INC103", "survival_duration"].iloc[0] == pytest.approx(6.0)
    assert result.loc[result["incident_id"] == "INC103", "survival_event"].iloc[0] == 1


def test_censoring_boundary_conditions_use_fixed_cutoff_for_active_records():
    df = pd.DataFrame([
        {"customer_id": "SUB901", "timestamp": "2026-06-01", "state": "Active"},
        {"customer_id": "SUB901", "timestamp": "2026-06-10", "state": "Canceled"},
        {"customer_id": "SUB902", "timestamp": "2026-06-01", "state": "Active"},
        {"customer_id": "SUB902", "timestamp": "2026-06-15", "state": "Active"},
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    cutoff = pd.Timestamp("2026-06-21")
    config = _build_survival_config(
        subject_id_col="customer_id",
        terminal_states=["Canceled"],
        censored_states=[],
        observation_window={
            "start_mode": "subject_first",
            "fixed_start_date": None,
            "end_mode": "fixed_cutoff",
            "fixed_end_date": cutoff,
        },
    )

    preparer = SurvivalDataPreparer.from_config_dict(config)
    result = preparer.transform(df)

    assert result.loc[result["customer_id"] == "SUB901", "survival_duration"].iloc[0] == pytest.approx(9.0)
    assert result.loc[result["customer_id"] == "SUB901", "survival_event"].iloc[0] == 1
    assert result.loc[result["customer_id"] == "SUB902", "survival_duration"].iloc[0] == pytest.approx(20.0)
    assert result.loc[result["customer_id"] == "SUB902", "survival_event"].iloc[0] == 0


def test_invalid_dataset_without_subject_or_timestamp_columns_is_rejected():
    invalid_data = pd.DataFrame([
        {"setting_name": "max_connections", "configured_value": "100", "environment": "Production"},
        {"setting_name": "timeout_limit", "configured_value": "30", "environment": "Production"},
        {"setting_name": "retry_policy", "configured_value": "exponential", "environment": "Staging"},
    ])

    config = _build_survival_config()
    preparer = SurvivalDataPreparer.from_config_dict(config)

    with pytest.raises(KeyError, match="Input data is missing required columns"):
        preparer.transform(invalid_data)
