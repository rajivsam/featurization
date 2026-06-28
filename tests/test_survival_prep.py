import pandas as pd
import pytest

from tabular.survival_prep import SurvivalDataPreparer


def _build_config(**overrides):
    base = {
        "subject_id_col": "subject_id",
        "timestamp_col": "event_timestamp",
        "state_col": "event_state",
        "terminal_states": ["Resolved", "Closed"],
        "censored_states": ["Canceled"],
        "observation_window": {
            "start_mode": "subject_first",
            "fixed_start_date": None,
            "end_mode": "dataset_max",
            "fixed_end_date": None,
        },
        "static_features": ["caller_id"],
        "dynamic_aggregation_rules": {"priority": "first", "reassignment_count": "max"},
    }
    base.update(overrides)
    return base


def test_survival_prep_generates_duration_and_event_flags():
    df = pd.DataFrame([
        {"subject_id": "A", "event_timestamp": "2026-01-01 08:00", "event_state": "New", "caller_id": "X", "priority": 1, "reassignment_count": 0},
        {"subject_id": "A", "event_timestamp": "2026-01-03 10:30", "event_state": "Resolved", "caller_id": "X", "priority": 1, "reassignment_count": 2},
        {"subject_id": "A", "event_timestamp": "2026-01-05 12:00", "event_state": "Closed", "caller_id": "Y", "priority": 2, "reassignment_count": 5},
        {"subject_id": "B", "event_timestamp": "2026-01-02 09:00", "event_state": "New", "caller_id": "Z", "priority": 3, "reassignment_count": 1},
        {"subject_id": "B", "event_timestamp": "2026-01-04 17:00", "event_state": "Canceled", "caller_id": "Z", "priority": 3, "reassignment_count": 4},
    ])

    preparer = SurvivalDataPreparer.from_config_dict(_build_config())
    result = preparer.transform(df)

    assert set(result.columns) >= {"subject_id", "survival_duration", "survival_event", "caller_id", "priority", "reassignment_count"}
    row_a = result.loc[result.subject_id == "A"].iloc[0]
    assert row_a.survival_event == 1
    assert row_a.caller_id == "X"
    assert row_a.priority == 1
    assert row_a.reassignment_count == 2
    assert pytest.approx(row_a.survival_duration, rel=1e-3) == 50.5 / 24

    row_b = result.loc[result.subject_id == "B"].iloc[0]
    assert row_b.survival_event == 0
    assert row_b.caller_id == "Z"
    assert row_b.reassignment_count == 4
    assert pytest.approx(row_b.survival_duration, rel=1e-3) == 2.3333333333


def test_survival_prep_observation_window_fixed_start_and_cutoff():
    df = pd.DataFrame([
        {"subject_id": "C", "event_timestamp": "2026-01-01 06:00", "event_state": "New", "caller_id": "A", "priority": 1, "reassignment_count": 0},
        {"subject_id": "C", "event_timestamp": "2026-01-05 08:00", "event_state": "In Progress", "caller_id": "A", "priority": 2, "reassignment_count": 1},
    ])

    config = _build_config(
        observation_window={
            "start_mode": "fixed_calendar",
            "fixed_start_date": "2026-01-03 00:00",
            "end_mode": "fixed_cutoff",
            "fixed_end_date": "2026-01-06 00:00",
        }
    )
    preparer = SurvivalDataPreparer.from_config_dict(config)
    result = preparer.transform(df)

    assert len(result) == 1
    row = result.iloc[0]
    assert row.survival_event == 0
    assert pytest.approx(row.survival_duration, rel=1e-3) == 3.0
    assert row.caller_id == "A"
    assert row.priority == 2


def test_survival_prep_uses_dataset_max_for_implicit_censoring():
    df = pd.DataFrame([
        {"subject_id": "D", "event_timestamp": "2026-01-01 00:00", "event_state": "New", "caller_id": "M", "priority": 1, "reassignment_count": 0},
        {"subject_id": "D", "event_timestamp": "2026-01-02 00:00", "event_state": "In Progress", "caller_id": "M", "priority": 2, "reassignment_count": 1},
        {"subject_id": "E", "event_timestamp": "2026-01-03 00:00", "event_state": "New", "caller_id": "N", "priority": 1, "reassignment_count": 0},
    ])

    preparer = SurvivalDataPreparer.from_config_dict(_build_config())
    result = preparer.transform(df)

    assert result.loc[result.subject_id == "D", "survival_event"].iloc[0] == 0
    assert result.loc[result.subject_id == "E", "survival_event"].iloc[0] == 0
    assert result.loc[result.subject_id == "E", "survival_duration"].iloc[0] == pytest.approx(0.0)


def test_survival_prep_rejects_duplicate_state_classification():
    config = _build_config(
        censored_states=["Resolved", "Canceled"],
    )
    with pytest.raises(ValueError, match="ERR_DUPLICATE_CLASS"):
        SurvivalDataPreparer.from_config_dict(config)


def test_survival_prep_requires_repeated_subject_ids():
    df = pd.DataFrame([
        {"subject_id": "F", "event_timestamp": "2026-01-01 00:00", "event_state": "New", "caller_id": "X", "priority": 1, "reassignment_count": 0},
        {"subject_id": "G", "event_timestamp": "2026-01-02 00:00", "event_state": "Resolved", "caller_id": "Y", "priority": 2, "reassignment_count": 1},
    ])

    preparer = SurvivalDataPreparer.from_config_dict(_build_config())
    with pytest.raises(ValueError, match="ERR_ID_NOT_REPEATED"):
        preparer.transform(df)
