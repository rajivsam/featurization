## Unified System Design Document: Generic Survival Analysis Data Preparation Tool

## 1. Introduction & Core Objectives

Survival analysis requires tracking the exact time duration until a terminal event occurs, while gracefully accounting for right-censoring. This document serves as the master engineering specification for a Generic Survival Analysis Data Preparation Tool. It outlines the input models, the interactive wizard interface, the mathematical transformation engine, and the final output schemas required to turn raw transactional logs into analysis-ready datasets.

------------------------------

## 2. Input Data Architectural Models
The system architecture natively supports three distinct configurations of input data schemas:

  +-----------------------------------------------------------------------+

  |                             INPUT CHANNELS                            |
  +-------------------+-------------------+-------------------------------+

                      |                   |
                      v                   v
            +-------------------+       +-------------------------------+

            |  RAW EVENT LOG    |       | INTERVALLIC LONG FORM         |
            +---------+---------+       +---------------+---------------+

                      |                                 |
                      | (Transformation Engine)         | (Interval Validation)
                      v                                 v
  +-----------------------------------------------------------------------+

  |                     STRUCTURAL SUMMARY WIDE FORM                  |
  |             (Target State: Exactly One Row Per Subject ID)             |
  +-----------------------------------------------------------------------+


* Raw Event Logs (Process-Centric): Multiple chronological transaction rows tracking state transitions per single unique entity (e.g., UCI Incident Management Dataset ID 498).
* InterVallic Long Form (Counting Process): Multiple rows per subject tracking consecutive time-varying interval blocks (Start, Stop] where individual features remain constant.
* Structural Summary Wide Form (Baseline Target): Exactly one row mapping to one unique subject, containing baseline static identifiers alongside explicit duration and event fields.

------------------------------

## 3. Interactive Configuration Wizard Flow
To construct a valid configuration dynamically, the system executes an onboarding workflow driven by programmatic scanning of the raw data.
## Step 1: Data Ingest & Structural Profiling

* System Action: Profiles file extensions and reads row distributions. Extracts header lists and checks data types (Alphanumeric, Numeric, Datetime, Categorical).
* Interface Dialogue:

"File imported successfully (245,828 rows detected). Please choose how your columns are currently structured:"
[•] Raw Event Log | [ ] Summary Data Table | [ ] Time-Varying Interval Logs

[1] 

## Step 2: Backbone Mapping

* Interface Dialogue:

"Please map your tracking identifiers from the table columns below:"
* Unique Subject Key: [ Dropdown Selection (e.g., number) ]
   * Clock Timestamp Column: [ Dropdown Selection (e.g., sys_updated_at) ]
   * Process State Column: [ Dropdown Selection (e.g., incident_state) ] [2] 


## Step 3: Define Observation Boundaries

* System Action: Executes a fast min/max scan across the designated timestamp column to inject actual limits.
* Interface Dialogue:

"Your dataset timestamps span from 2024-01-01 to 2026-06-01. Choose your observation boundaries:"
* When does tracking begin?
   (*) Individually when each subject first enters the log
   ( ) At a fixed starting date across all entries [ YYYY-MM-DD ]
   * When does your study window officially close?
   (*) Automatically at the maximum dataset timestamp (2026-06-01)
   ( ) On a custom historical cutoff date [ YYYY-MM-DD ]


## Step 4: Map State Targets

* System Action: Runs an isolated unique value extraction across the state column.
* Interface Dialogue:

"We identified the following individual activities/states in your dataset.
* Select the state(s) representing a Terminal Event (Death/Resolution):
   [ ] New [ ] Active [X] Resolved [X] Closed
   * Select the state(s) representing an Explicit Cancellation/Drop:
   [ ] New [ ] Awaiting Vendor [X] Canceled


## Step 5: Feature Aggregation Configurator

* Interface Dialogue:

"Select your compression rules for flattening shifting transaction rows:"
* Static/Baseline columns (Defaults to pulling initial value): [ Multi-Select Dropdown: caller_id, location ]
   * Choose aggregation rules for dynamic numeric fields:
   priority -------------> [ First Value ▼ ]
   reassignment_count ---> [ Maximum Code ▼ ]


------------------------------
## 4. The Core Universal Configuration Schema
The wizard saves the inputs above into a strict, validated JSON metadata format:

{
  "$schema": "https://json-schema.org",
  "title": "SurvivalPrepConfig",
  "type": "object",
  "required": ["subject_id_col", "timestamp_col", "state_col", "terminal_states", "observation_window"],
  "properties": {
    "subject_id_col": { "type": "string" },
    "timestamp_col": { "type": "string" },
    "state_col": { "type": "string" },
    "terminal_states": { "type": "array", "items": { "type": "string" } },
    "censored_states": { "type": "array", "items": { "type": "string" } },
    "observation_window": {
      "type": "object",
      "required": ["start_mode", "fixed_start_date", "end_mode", "fixed_end_date"],
      "properties": {
        "start_mode": { "type": "string", "enum": ["subject_first", "fixed_calendar"] },
        "fixed_start_date": { "type": ["string", "null"], "format": "date" },
        "end_mode": { "type": "string", "enum": ["dataset_max", "fixed_cutoff"] },
        "fixed_end_date": { "type": ["string", "null"], "format": "date" }
      }
    },
    "static_features": { "type": "array", "items": { "type": "string" } },
    "dynamic_aggregation_rules": {
      "type": "object",
      "additionalProperties": { "type": "string", "enum": ["first", "last", "max", "min", "sum", "mode"] }
    }
  }
}

------------------------------
## 5. Mathematical Transformation Engine (Input-to-Output Mapping)
When the transformation runs on a Raw Event Log, the engine applies a structured 4-stage pipeline to map the multiple rows of input data into a single survival timeline per subject.
## Phase 1: Temporal Truncation & Filtering
The engine filters out records outside the valid study window to prevent historical bias and forward-looking data leakage.

* If fixed_start_date is provided: Drop any rows where $Timestamp < fixed\_start\_date$.
* If fixed_end_date is provided: Drop any rows where $Timestamp > fixed\_end\_date$.

## Phase 2: Define Timeline Extents ($T_{start}$ and $T_{end}$)
For each isolated group of rows belonging to a unique Subject_ID, sort chronologically by timestamp_col and compute boundaries:
$$\text{Let } \text{Log}_{sub} = \text{Chronologically sorted rows for a specific Subject ID}$$ 

   1. Calculate Origin ($T_{start}$):
   * If start_mode is "subject_first", $T_{start} = \text{Minimum timestamp found in } \text{Log}_{sub}$.
      * If start_mode is "fixed_calendar", $T_{start} = \text{fixed\_start\_date}$.
   2. Locate Terminal Event Row ($R_{term}$):
   * Scan $\text{Log}_{sub}$ in chronological order. Find the first row where the state_col value exists inside the user-defined terminal_states array.
   3. Calculate Terminal/Censoring Boundary ($T_{end}$):
   * Scenario A (Event Occurred): If a terminal row ($R_{term}$) is found, $T_{end} = \text{Timestamp of } R_{term}$.
      * Scenario B (Explicit Censoring): If no terminal row is found, but the last chronological row in $\text{Log}_{sub}$ has a state inside censored_states, $T_{end} = \text{Timestamp of that last row}$.
      * Scenario C (Implicit Right-Censoring): If neither Scenario A nor B is met, the subject is still alive/pending.
      * If end_mode is "dataset_max", $T_{end} = \text{Global maximum timestamp of the entire dataset}$.
         * If end_mode is "fixed_cutoff", $T_{end} = \text{fixed\_end\_date}$.
      
## Phase 3: Calculate Duration and Event Indicators
Using the values extracted in Phase 2, calculate the two essential target vectors for survival modeling:
$$\text{Duration} = T_{end} - T_{start}$$ 
$$\text{Event} = \begin{cases} 1 & \text{if } T_{end} \text{ was established via Scenario A (Terminal State hit)} \\ 0 & \text{if } T_{end} \text{ was established via Scenario B or C (Censored)} \end{cases}$$ 

## Phase 4: Covariate Flattening

For columns flagged in static_features or dynamic_aggregation_rules, the engine extracts data rows up to but not exceeding $T_{end}$ (to prevent post-event feature leakage). It applies the mapped function (first, last, max, min, sum, mode) to squash the timeline into a single row.

------------------------------
## 6. Output Table Schema & Preview Specifications
The output of the tool is a tabular file (CSV or Parquet) containing exactly one row per unique Subject ID. [3] 
## Strict Output Columns Blueprint

   1. [subject_id_col]: Retained string/alphanumeric unique tracking identifier key.
   2. survival_duration: Numeric float tracking time elapsed. Units are dynamically determined based on scale (e.g., Hours, Days).
   3. survival_event: Binary integer (1 or 0) representing event occurrence vs censoring.
   4. [feature_cols...]: Flattened static metrics and aggregated dynamic features.

## Output Visual Interface & Summary Dashboard
Before downloading the full file, the tool displays an analysis readiness dashboard featuring:
## Data Table Preview Matrix

| ticket_id (ID) | survival_duration (Days) | survival_event (Binary) | initial_priority (Static) | reassignment_count (Max) |
|---|---|---|---|---|
| INC0000045 | 4.21 | 1 | 2 - High | 3 |
| INC0000047 | 12.00 | 0 | 3 - Moderate | 1 |
| INC0000052 | 0.45 | 1 | 1 - Critical | 0 |

## Survival Profiler Summary Metrics

* Total Sample Size ($N$): Number of uniquely processed subjects.
* Censoring Rate: Percentage of the cohort that did not experience the event ($\frac{\sum (\text{Event}==0)}{N} \times 100$).
* Event Density: Total number of observed terminal occurrences.
* Timeline Distribution: Shortest vs longest duration observed in the output pipeline.

------------------------------
## 7. Error State Messages & Validation Rules

| Target Step | Error Code | Interface Warning Message | Trigger Condition |
|---|---|---|---|
| Step 2 | ERR_ID_NOT_REPEATED | "The chosen subject column contains only unique values. An Event Log requires multiple recurring rows per ID to calculate timelines." | Every row has a 100% unique ID token while input type is set to Event Log. |
| Step 3 | ERR_WINDOW_OUT_OF_BOUNDS | "The custom cutoff date entered falls completely outside the timestamps present in your file data. Choose a date between [Min] and [Max]." | fixed_end_date is structurally completely disconnected from the file timeline. |
| Step 4 | ERR_DUPLICATE_CLASS | "State value '[Value]' cannot represent a Terminal Event and a Censored Event at the same time. Please uncheck one option." | The same checkbox value is triggered across both categorical questions. |
| Step 5 | ERR_UNMAPPED_FEATURE | "The column '[Column]' has not been assigned a compression rule. It will be excluded from final modelling unless mapped." | A metadata column was left unassigned to either static lists or aggregation rules. |

With the comprehensive design document fully unified, would you like to build the backend conversion class in Python that implements this mathematical transformation pipeline, or should we design a mock file generator to generate sample event log rows for testing?

[1] [https://help.anthology.com](https://help.anthology.com/ENG/content/help/importcontandtestscore.htm)
[2] [https://help.viedoc.net](https://help.viedoc.net/c/e311e6/fa7777/en/)
[3] [https://towardsdatascience.com](https://towardsdatascience.com/automated-testing-a-software-engineering-concept-data-scientists-must-know-to-succeed/)
