## Test Case 1: Raw Event Log with Terminal Events (ITSM Style)
This test sample models three distinct subjects using an event-log format to prove your engine handles multiple rows, chronological sorting, and discrete state milestones correctly.

## Input DataFrame Generator

import pandas as pd

# Simulates a raw event log tracking the life cycle of IT support incidents

log_data_input = pd.DataFrame([
    # INC101: Smooth lifecycle. Lasts exactly 4 days. Hits terminal 'Closed' state.
    {"incident_id": "INC101", "timestamp": "2026-01-01 09:00:00", "state": "New", "priority": "High"},
    {"incident_id": "INC101", "timestamp": "2026-01-03 14:00:00", "state": "Active", "priority": "High"},
    {"incident_id": "INC101", "timestamp": "2026-01-05 09:00:00", "state": "Closed", "priority": "High"},
    
    # INC102: Rapid resolution turnaround path. Lasts exactly 1 day. Hits terminal 'Resolved' state.
    {"incident_id": "INC102", "timestamp": "2026-01-02 10:00:00", "state": "New", "priority": "Critical"},
    {"incident_id": "INC102", "timestamp": "2026-01-03 10:00:00", "state": "Resolved", "priority": "Critical"},
    
    # INC103: Non-chronological sequence error check (should be sorted internally by the tool)
    {"incident_id": "INC103", "timestamp": "2026-01-08 12:00:00", "state": "Closed", "priority": "Low"}, # End row out of order
    {"incident_id": "INC103", "timestamp": "2026-01-02 12:00:00", "state": "New", "priority": "Low"},    # Start row out of order
])
log_data_input['timestamp'] = pd.to_datetime(log_data_input['timestamp'])

## Operational Configuration Parameters

* subject_col: "incident_id"
* terminal_states: {"Closed", "Resolved"}
* start_time_extractor: Minimum timestamp per group.
* end_time_extractor: Earliest timestamp matching a terminal state.

## Target Output Verification Matrix

If mapped correctly, your IntermediateSurvivalEngine must yield exactly this DataFrame output:

| subject_id | duration | event_observed |
|---|---|---|
| INC101 | 4 | 1 |
| INC102 | 1 | 1 |
| INC103 | 6 | 1 |

------------------------------
## Test Case 2: Right-Censoring Boundary Conditions

This dataset tests how your system handles open, incomplete, or dropped records. It introduces an explicit censoring cutoff boundary to measure subjects that survived beyond the study observation window. [1] 

## Input DataFrame Generator

# Simulates a customer subscription database tracking account status changes
censored_data_input = pd.DataFrame([
    # SUB901: Explicit withdrawal cancellation event state
    {"customer_id": "SUB901", "last_updated": "2026-06-01", "status": "Active"},
    {"customer_id": "SUB901", "last_updated": "2026-06-10", "status": "Canceled"},
    
    # SUB902: Active customer that never cancels. Reaches the maximum study cutoff boundary alive.
    {"customer_id": "SUB902", "last_updated": "2026-06-01", "status": "Active"},
    {"customer_id": "SUB902", "last_updated": "2026-06-15", "status": "Active"},
])
censored_data_input['last_updated'] = pd.to_datetime(censored_data_input['last_updated'])
# Global explicit study boundary limit setup 

STUDY_END_CUTOFF = pd.Timestamp("2026-06-21")

## Operational Configuration Parameters

* subject_col: "customer_id"
* terminal_states: {"Canceled"}
* start_time_extractor: Minimum timestamp per group.
* end_time_extractor: If terminal state exists, extract its timestamp. Else, return STUDY_END_CUTOFF.

## Target Output Verification Matrix
If mapped correctly, your engine must output a 0 (censored) event code for the active customer, computing their duration up to the final study day boundary line:

| subject_id | duration | event_observed |
|---|---|---|
| SUB901 | 9 | 1 |
| SUB902 | 20 | 0 |

------------------------------
## Test Case 3: Complete Failure Validation (Amenability Test)
This sample contains no columns that map to subject IDs or timeline tracking metrics. Use it to explicitly test that your KMDSValidationAgent halts execution with a clean exit status instead of crashing mid-calculation.
## Input DataFrame Generator

# Static system configurations with no discernible time metric vectors or entity identifiersinvalid_data_input = pd.DataFrame([
    {"setting_name": "max_connections", "configured_value": "100", "environment": "Production"},
    {"setting_name": "timeout_limit", "configured_value": "30", "environment": "Production"},
    {"setting_name": "retry_policy", "configured_value": "exponential", "environment": "Staging"}
])

## Expected System Behavior
When passing invalid_data_input through the tool, the script must intercept the runtime pipeline, print your specific standard error output block, and issue a system terminate signal (sys.exit(1)):

================================================================================
CRITICAL NOTICE: It looks like this dataset is not amenable for a survival analysis computation.
If you believe that this is true, please update your data dictionary to explicitly say that a field is a candidate subject field.
You can then update the meta-data generation by running dd-parser-cleaner again on the dataset and then try running this utility again.
================================================================================
Process finished with exit code 1


