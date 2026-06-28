# Survival Analysis Featurization Pipeline Wiring

This document describes how to wire `featurization_scripts/featurization.py` and the package-level survival preparation utility into a pipeline that transforms:

- a raw event log,
- an interval long-form dataset, or
- a structural wide-form dataset

into one survival-ready table with one row per subject.

> Note: This implementation is provided as a survival-specific example, not a one-size-fits-all feature for every featurization pipeline. Users should initialize their agent on the correct documentation and then adapt pipeline stages to the needs of their own use case.

## 1. Pipeline contract

The package pipeline contract is:

- stage signature: `method(context, stage_cfg) -> pd.DataFrame`
- stage output: a `DataFrame` aligned to the current survivor universe index
- pipeline execution: `src/featurization/core/sequential_pipeline_runner.py`
- final outputs: `featurized_data.csv` and `model_ready_numeric_data.csv`

For survival preparation, the stage wrapper should stay thin and delegate reusable logic to `src/tabular/survival_prep.py`.

## 2. Supported input forms

### 2.1 Event Log

A raw event log contains many rows per subject, ordered by timestamp, with state transitions or activity records.

Required columns:

- `subject_id` or equivalent key column
- `event_timestamp` or equivalent timestamp column
- `event_state` or equivalent state column

This is the canonical source for the survival preparer. The stage should group by subject, compute start/end bounds, and flatten features.

### 2.2 Interval Long Form

An interval long-form dataset contains time-varying observations per subject, where each row represents a time interval block.

Required columns are the same as the event log plus interval-specific covariates. The preparer can treat each interval row as an event-record row and aggregate before the survival boundary.

### 2.3 Structural Wide Form

A wide-form dataset already has one row per subject with explicit duration and event fields.

This form can be forwarded to later featurization stages without the survival prep stage, or optionally validated with a lightweight wrapper to ensure the survival target schema is present.

## 3. Recommended config anchors

Add a survival preprocessing stage to `featurizer_config.yaml` or your workspace config. This sample wiring is intended as a starting point for survival use cases; it should be adapted to the specific dataset and business requirements.

```yaml
pipeline:
  - name: Survival Data Preparation
    method: survival_data_preparation
    entity: System
    sub_filter: Survival
    subject_id_col: subject_id
    timestamp_col: event_timestamp
    state_col: event_state
    terminal_states:
      - Resolved
      - Closed
    censored_states:
      - Canceled
    observation_window:
      start_mode: subject_first
      fixed_start_date: null
      end_mode: dataset_max
      fixed_end_date: null
    static_features:
      - caller_id
      - customer_segment
    dynamic_aggregation_rules:
      priority: first
      reassignment_count: max
      score: last
```

This stage config is intentionally minimal so the wrapper can translate it into the package utility config.

## 3.1 Survival config glossary

- `subject_id_col`: the unique subject identifier column used to group event rows into one survival record.
- `timestamp_col`: the datetime column used to order events and compute start/end boundaries.
- `state_col`: the state or status column used to identify terminal or censored outcomes.
- `terminal_states`: a list of state values that indicate the subject experienced the event of interest.
- `censored_states`: a list of state values that indicate an explicit censoring event which ends the subject timeline without the terminal event. This still produces a row in the output with `survival_event = 0`; it is not left-censoring.
- `observation_window`: a nested object controlling how the timeline is bounded:
  - `start_mode`: `subject_first` to use each subject's first observed timestamp, or `fixed_calendar` to use a fixed cohort start date.
  - `fixed_start_date`: required when `start_mode` is `fixed_calendar`; defines the common start date for all subjects.
  - `end_mode`: `dataset_max` to censor at the dataset maximum timestamp, or `fixed_cutoff` to censor at a fixed cutoff date.
  - `fixed_end_date`: required when `end_mode` is `fixed_cutoff`; defines the shared censoring cutoff date.
- `static_features`: columns whose first observed value is preserved as baseline covariates.
- `dynamic_aggregation_rules`: a dictionary that maps time-varying input columns to aggregation functions applied over rows up to the survival endpoint. Supported functions are `first`, `last`, `max`, `min`, `sum`, and `mode`.
  - `first`: preserves the earliest observed value before or at `T_end`.
  - `last`: preserves the latest value before or at `T_end`.
  - `max`: returns the maximum value observed before or at `T_end`.
  - `min`: returns the minimum value observed before or at `T_end`.
  - `sum`: returns the sum of values observed before or at `T_end`.
  - `mode`: returns the most frequent value observed before or at `T_end`; when there is a tie, the first mode is chosen.
  - All aggregations are applied only to rows whose timestamp is `<= T_end`, ensuring no post-event leakage.
- `duration_unit` (optional): if provided, forces the output `survival_duration` unit to one of `seconds`, `minutes`, `hours`, or `days`. If omitted, the pipeline infers the unit from the observed duration scale.

### 3.1.1 `dynamic_aggregation_rules` example

Suppose a support ticket event log has these columns:

- `incident_id`
- `event_timestamp`
- `state`
- `priority`
- `reassignment_count`
- `customer_segment`

A rule set like this preserves the first priority, counts reassignment activity, and captures the final customer segment before the outcome:

```yaml
dynamic_aggregation_rules:
  priority: first
  reassignment_count: sum
  customer_segment: last
```

For subject `INC101` with rows:

| event_timestamp | priority | reassignment_count | customer_segment |
|---|---|---|---|
| 2026-01-01 09:00 | High | 0 | Commercial |
| 2026-01-03 14:00 | High | 2 | Commercial |
| 2026-01-05 09:00 |  | 1 | Enterprise |

The flattened survival row would contain:

- `priority = High`
- `reassignment_count = 3`
- `customer_segment = Enterprise`

because only rows occurring on or before `T_end` are aggregated.

### 3.2 Survival config example

```yaml
pipeline:
  - name: Survival Data Preparation
    method: survival_data_preparation
    entity: System
    sub_filter: Survival
    subject_id_col: subject_id
    timestamp_col: event_timestamp
    state_col: event_state
    terminal_states:
      - Resolved
      - Closed
    censored_states:
      - Canceled
    observation_window:
      start_mode: subject_first
      fixed_start_date: null
      end_mode: dataset_max
      fixed_end_date: null
    static_features:
      - caller_id
      - customer_segment
    dynamic_aggregation_rules:
      priority: first
      reassignment_count: max
      score: last
    duration_unit: days
```

### 3.3 Censoring semantics

- `censored_states` is intended to capture explicit censoring states that terminate the subject timeline without the terminal event.
- When a subject reaches one of these values, the pipeline outputs a row with `survival_event = 0` and uses the timestamp of that censoring row as `T_end`.
- This is not left-censoring; it is an explicit form of right-censoring expressed in the event/state stream.
- If the dataset instead requires implicit censoring logic (for example, censoring subjects at a dataset cutoff date when no explicit censor state appears), that behavior is controlled by `observation_window.end_mode` rather than `censored_states`.
- Implicit censoring rules should be defined in the wrapper or preprocessing logic only if they are outside the standard `observation_window` contract. The package utility currently assumes explicit censor state values plus the configured end-mode semantics.

## 4. Example stage wrapper in `featurization_scripts/featurization.py`

```python
import pandas as pd
from tabular.survival_prep import SurvivalDataPreparer


def survival_data_preparation(context: dict, stage_cfg: dict) -> pd.DataFrame:
    """Pipeline stage wrapper for survival data preparation."""
    data = context["data"]

    survival_config = {
        "subject_id_col": stage_cfg.get("subject_id_col", "subject_id"),
        "timestamp_col": stage_cfg.get("timestamp_col", "event_timestamp"),
        "state_col": stage_cfg.get("state_col", "event_state"),
        "terminal_states": stage_cfg.get("terminal_states", []),
        "censored_states": stage_cfg.get("censored_states", []),
        "observation_window": stage_cfg.get("observation_window", {}),
        "static_features": stage_cfg.get("static_features", []),
        "dynamic_aggregation_rules": stage_cfg.get("dynamic_aggregation_rules", {}),
    }

    preparer = SurvivalDataPreparer.from_config_dict(survival_config)
    output_df = preparer.transform(data)

    # Keep the subject key as a column and allow the caller to promote it later.
    return output_df
```

### 4.1 Notes on the wrapper

- Do not mutate `context["data"]` in place.
- Keep stage logic shallow: configuration parsing + call into `SurvivalDataPreparer`.
- If the dataset does not already have `subject_id` as the index, return the subject key as a column.

## 5. Branching by input shape

### 5.1 Raw event log path

1. Load raw event log from the workspace input path configured in `featurizer_config.yaml`.
2. Apply any data-quality stage wrappers needed for date parsing or state normalization.
3. Run `survival_data_preparation`.
4. Follow with feature-engineering stages on the flattened survival output.

### 5.2 Interval long form path

1. Load interval-form records.
2. Normalize each interval to use the same key/timestamp/state schema.
3. Run the same `survival_data_preparation` stage.

The preprocessing wrapper may need to collapse interval-specific row delimiters into a canonical timestamp/order field before passing data to `SurvivalDataPreparer`.

### 5.3 Structural wide form path

If the workspace already has one row per subject and explicit
`survival_duration`/`survival_event` columns, do not use `survival_data_preparation`.
Instead, use a downstream feature-selection or modeling wrapper that accepts the existing survival target.

Example config for the wide form:

```yaml
pipeline:
  - name: Survival Feature Projection
    method: harmonize_and_project_feature_space
    entity: System
    sub_filter: Survival
    target_col: survival_event
    split_col: dataset_split
```

## 6. Output schema contract

The survival preparation stage should produce a table with exactly one row per subject and at least these columns:

- `subject_id` (or configured subject identifier)
- `survival_duration`
- `survival_event`
- any static feature columns
- any aggregated dynamic feature columns

This output can then feed downstream featurization stages for encoding, selection, and train/val split.

## 7. Leakage-safe transformation guidance

The survival prep stage should enforce these rules:

- compute `T_start` from subject first exposure or fixed calendar start only
- compute `T_end` from the first terminal event, explicit censoring, or dataset maximum
- aggregate only rows whose timestamp is `<= T_end`
- fit artifacts downstream on train only, not on validation or active rows

## 8. Example pipeline topology

For an event log workload, a full surviving pipeline might look like:

```yaml
pipeline:
  - name: Survival Data Preparation
    method: survival_data_preparation
    entity: System
    sub_filter: Survival
    subject_id_col: subject_id
    timestamp_col: event_timestamp
    state_col: event_state
    terminal_states: [Resolved, Closed]
    censored_states: [Canceled]
    observation_window:
      start_mode: subject_first
      fixed_start_date: null
      end_mode: dataset_max
      fixed_end_date: null
    static_features: [caller_id, customer_segment]
    dynamic_aggregation_rules:
      priority: first
      reassignment_count: max

  - name: Survival Feature Encoding
    method: prepare_categorical_data
    entity: categorical
    sub_filter: survival

  - name: Survival Feature Selection
    method: harmonize_and_project_feature_space
    entity: System
    sub_filter: survival
    target_col: survival_event
    split_col: dataset_split
```

For a wide-form dataset, remove the first stage and start from feature encoding.

## 9. Implementation checklist

- [ ] Add `survival_data_preparation` to `featurization_scripts/featurization.py`
- [ ] Add survival stage config to `featurizer_config.yaml`
- [ ] Keep static/dynamic feature lists explicit in stage config
- [ ] Validate stage output schema before downstream stages
- [ ] Preserve `index=False` persistence semantics for final CSV artifacts

## 10. Troubleshooting

Common failure modes:

- missing `subject_id` or timestamp/state columns in the input
- duplicate subject IDs not present in raw event-log mode
- fixed window dates outside the dataset timeline
- dynamic aggregation columns absent from the raw rows

If a dataset is already wide-form, do not rerun survival preparation; instead, treat it as a downstream modeling input.
