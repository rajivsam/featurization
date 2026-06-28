from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

VALID_DURATION_UNITS = {"seconds", "minutes", "hours", "days"}
VALID_START_MODES = {"subject_first", "fixed_calendar"}
VALID_END_MODES = {"dataset_max", "fixed_cutoff"}
VALID_AGGREGATIONS = {"first", "last", "max", "min", "sum", "mode"}


@dataclass
class SurvivalPrepConfig:
    subject_id_col: str
    timestamp_col: str
    state_col: str
    terminal_states: list[str]
    censored_states: list[str]
    observation_window: dict[str, Any]
    static_features: list[str]
    dynamic_aggregation_rules: dict[str, str]
    duration_unit: str | None = None

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "SurvivalPrepConfig":
        if config is None:
            raise ValueError("Survival config is required.")

        required_keys = [
            "subject_id_col",
            "timestamp_col",
            "state_col",
            "terminal_states",
            "observation_window",
        ]
        missing = [key for key in required_keys if key not in config]
        if missing:
            raise KeyError(f"Missing required survival config keys: {missing}")

        return cls(
            subject_id_col=str(config["subject_id_col"]),
            timestamp_col=str(config["timestamp_col"]),
            state_col=str(config["state_col"]),
            terminal_states=list(config.get("terminal_states", [])),
            censored_states=list(config.get("censored_states", [])),
            observation_window=dict(config["observation_window"]),
            static_features=list(config.get("static_features", [])),
            dynamic_aggregation_rules=dict(config.get("dynamic_aggregation_rules", {})),
            duration_unit=(str(config["duration_unit"]).lower().strip()
                           if config.get("duration_unit") is not None
                           else None),
        )

    def validate(self) -> None:
        if not self.subject_id_col:
            raise ValueError("subject_id_col must be provided.")
        if not self.timestamp_col:
            raise ValueError("timestamp_col must be provided.")
        if not self.state_col:
            raise ValueError("state_col must be provided.")
        if not self.terminal_states:
            raise ValueError("terminal_states must contain at least one state.")

        if self.duration_unit is not None and self.duration_unit not in VALID_DURATION_UNITS:
            raise ValueError(
                f"duration_unit must be one of {sorted(VALID_DURATION_UNITS)}. "
                f"Received: '{self.duration_unit}'."
            )

        start_mode = self.observation_window.get("start_mode")
        end_mode = self.observation_window.get("end_mode")
        if start_mode not in VALID_START_MODES:
            raise ValueError(
                f"observation_window.start_mode must be one of {sorted(VALID_START_MODES)}. "
                f"Received: '{start_mode}'."
            )
        if end_mode not in VALID_END_MODES:
            raise ValueError(
                f"observation_window.end_mode must be one of {sorted(VALID_END_MODES)}. "
                f"Received: '{end_mode}'."
            )

        fixed_start_date = self.observation_window.get("fixed_start_date")
        fixed_end_date = self.observation_window.get("fixed_end_date")
        if start_mode == "fixed_calendar" and fixed_start_date is None:
            raise ValueError("observation_window.fixed_start_date is required when start_mode == 'fixed_calendar'.")
        if end_mode == "fixed_cutoff" and fixed_end_date is None:
            raise ValueError("observation_window.fixed_end_date is required when end_mode == 'fixed_cutoff'.")

        duplicate_states = set(self.terminal_states).intersection(set(self.censored_states or []))
        if duplicate_states:
            raise ValueError(
                "ERR_DUPLICATE_CLASS: State values cannot be both terminal and censored. "
                f"Duplicate values: {sorted(duplicate_states)}."
            )

        for agg_name in self.dynamic_aggregation_rules.values():
            if agg_name not in VALID_AGGREGATIONS:
                raise ValueError(
                    f"Unsupported aggregation '{agg_name}' in dynamic_aggregation_rules. "
                    f"Supported values: {sorted(VALID_AGGREGATIONS)}."
                )

    def normalized_observation_window(self) -> dict[str, Any]:
        result = {
            "start_mode": str(self.observation_window.get("start_mode", "subject_first")).strip(),
            "fixed_start_date": self._parse_optional_datetime(self.observation_window.get("fixed_start_date")),
            "end_mode": str(self.observation_window.get("end_mode", "dataset_max")).strip(),
            "fixed_end_date": self._parse_optional_datetime(self.observation_window.get("fixed_end_date")),
        }
        return result

    @staticmethod
    def _parse_optional_datetime(value: Any) -> pd.Timestamp | None:
        if value is None:
            return None
        if isinstance(value, pd.Timestamp):
            return value
        if isinstance(value, str):
            return pd.to_datetime(value, utc=False)
        return pd.to_datetime(value, utc=False)


class SurvivalDataPreparer:
    """Transforms raw event-log style data into survival-ready wide-form output."""

    def __init__(self, config: SurvivalPrepConfig):
        self.config = config
        self.config.validate()
        self.output_duration_unit: str | None = None

    @classmethod
    def from_config_dict(cls, config: dict[str, Any]) -> "SurvivalDataPreparer":
        return cls(SurvivalPrepConfig.from_dict(config))

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        if data is None:
            raise ValueError("Input data cannot be None.")
        if data.empty:
            return pd.DataFrame()

        required_columns = {
            self.config.subject_id_col,
            self.config.timestamp_col,
            self.config.state_col,
        }
        missing_cols = [c for c in required_columns if c not in data.columns]
        if missing_cols:
            raise KeyError(f"Input data is missing required columns: {missing_cols}")

        data = data.copy()
        data[self.config.timestamp_col] = pd.to_datetime(data[self.config.timestamp_col], utc=False)

        if data[self.config.subject_id_col].duplicated().sum() == 0:
            raise ValueError(
                "ERR_ID_NOT_REPEATED: The chosen subject column contains only unique values. "
                "A raw event log requires repeated rows per subject to calculate survival timelines."
            )

        normalized_window = self.config.normalized_observation_window()

        original_data_min = data[self.config.timestamp_col].min()
        original_data_max = data[self.config.timestamp_col].max()

        if normalized_window["fixed_start_date"] is not None:
            if normalized_window["fixed_start_date"] > original_data_max:
                raise ValueError(
                    "ERR_WINDOW_OUT_OF_BOUNDS: fixed_start_date falls after the latest timestamp in the dataset."
                )

        if normalized_window["fixed_end_date"] is not None:
            if normalized_window["fixed_end_date"] < original_data_min:
                raise ValueError(
                    "ERR_WINDOW_OUT_OF_BOUNDS: fixed_end_date falls before the earliest timestamp in the dataset."
                )

        data = self._apply_observation_window_filters(data, normalized_window)

        if data.empty:
            raise ValueError("No rows remain after applying the observation window filters.")

        dataset_max_timestamp = data[self.config.timestamp_col].max()
        subject_groups = data.groupby(self.config.subject_id_col, sort=False)

        rows: list[dict[str, Any]] = []
        durations = []

        for subject_id, group in subject_groups:
            group = group.sort_values(by=self.config.timestamp_col, ascending=True)
            if group.empty:
                continue

            start_timestamp = self._compute_start_timestamp(group, normalized_window)
            end_timestamp, event_flag = self._compute_end_timestamp(
                group, normalized_window, dataset_max_timestamp
            )

            if end_timestamp < start_timestamp:
                raise ValueError(
                    f"Computed end timestamp {end_timestamp} is before start timestamp {start_timestamp} "
                    f"for subject '{subject_id}'. Check your observation window settings."
                )

            elapsed = end_timestamp - start_timestamp
            durations.append(elapsed)

            records_to_aggregate = group[group[self.config.timestamp_col] <= end_timestamp]
            row = {
                self.config.subject_id_col: subject_id,
                "survival_event": int(event_flag),
            }
            row.update(self._extract_static_features(records_to_aggregate))
            row.update(self._extract_dynamic_features(records_to_aggregate))
            rows.append(row)

        if not rows:
            return pd.DataFrame(columns=[self.config.subject_id_col, "survival_duration", "survival_event"])

        result_df = pd.DataFrame(rows)
        self.output_duration_unit = self._determine_duration_unit(durations)
        result_df["survival_duration"] = [
            self._convert_timedelta(duration, self.output_duration_unit)
            for duration in durations
        ]
        result_df = result_df[[self.config.subject_id_col, "survival_duration", "survival_event"] + [c for c in result_df.columns if c not in {self.config.subject_id_col, "survival_duration", "survival_event"}]]
        return result_df

    def _apply_observation_window_filters(
        self,
        data: pd.DataFrame,
        normalized_window: dict[str, Any],
    ) -> pd.DataFrame:
        if normalized_window["fixed_start_date"] is not None:
            data = data[data[self.config.timestamp_col] >= normalized_window["fixed_start_date"]]
        if normalized_window["fixed_end_date"] is not None:
            data = data[data[self.config.timestamp_col] <= normalized_window["fixed_end_date"]]
        return data

    def _compute_start_timestamp(
        self,
        group: pd.DataFrame,
        normalized_window: dict[str, Any],
    ) -> pd.Timestamp:
        if normalized_window["start_mode"] == "fixed_calendar":
            return normalized_window["fixed_start_date"]
        return group[self.config.timestamp_col].iloc[0]

    def _compute_end_timestamp(
        self,
        group: pd.DataFrame,
        normalized_window: dict[str, Any],
        dataset_max_timestamp: pd.Timestamp,
    ) -> tuple[pd.Timestamp, bool]:
        terminal_mask = group[self.config.state_col].isin(self.config.terminal_states)
        if terminal_mask.any():
            most_recent_terminal = group.loc[terminal_mask, self.config.timestamp_col].iloc[0]
            return most_recent_terminal, True

        last_state = group[self.config.state_col].iloc[-1]
        if last_state in (self.config.censored_states or []):
            return group[self.config.timestamp_col].iloc[-1], False

        if normalized_window["end_mode"] == "fixed_cutoff":
            return normalized_window["fixed_end_date"], False
        return dataset_max_timestamp, False

    def _extract_static_features(self, group: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for column in self.config.static_features:
            if column not in group.columns:
                raise KeyError(f"Static feature column '{column}' not found in input data.")
            result[column] = group[column].iloc[0]
        return result

    def _extract_dynamic_features(self, group: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for column, agg in self.config.dynamic_aggregation_rules.items():
            if column not in group.columns:
                raise KeyError(f"Dynamic aggregation column '{column}' not found in input data.")
            values = group[column]
            result[column] = self._apply_aggregation(values, agg)
        return result

    @staticmethod
    def _apply_aggregation(values: pd.Series, agg: str) -> Any:
        if values.empty:
            return pd.NA
        agg = agg.lower().strip()
        if agg == "first":
            return values.iloc[0]
        if agg == "last":
            return values.iloc[-1]
        if agg == "max":
            return values.max()
        if agg == "min":
            return values.min()
        if agg == "sum":
            return values.sum()
        if agg == "mode":
            modes = values.mode(dropna=True)
            if modes.empty:
                return pd.NA
            return modes.iloc[0]
        raise ValueError(f"Unsupported aggregation function: {agg}")

    def _determine_duration_unit(self, durations: list[pd.Timedelta]) -> str:
        if self.config.duration_unit is not None:
            return self.config.duration_unit
        max_duration = max(durations)
        if max_duration.total_seconds() < 3600 * 48:
            return "hours"
        return "days"

    @staticmethod
    def _convert_timedelta(duration: pd.Timedelta, unit: str) -> float:
        if unit == "seconds":
            return float(duration.total_seconds())
        if unit == "minutes":
            return float(duration.total_seconds() / 60.0)
        if unit == "hours":
            return float(duration.total_seconds() / 3600.0)
        if unit == "days":
            return float(duration.total_seconds() / 86400.0)
        raise ValueError(f"Unsupported duration unit: {unit}")
