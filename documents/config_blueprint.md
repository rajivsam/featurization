# 📑 Configuration Guide: `featurizer_config.yaml` Reference Blueprint

The `featurizer_config.yaml` file serves as the authoritative single source of truth for the `kmds-data-helper` featurization workspace. It extends the core infrastructure established in the `dd-parser-cleaner` workflow to support the **Index-Centric Waterfall** pipeline.

---

## 🏗️ The 4 Major Configuration Sections

The file is split into four core blocks to logically decouple shared global system layers from individual runtime component boundaries.

```text
 ┌────────────────────────────────────────────────────────┐
 │ 🌐 GLOBAL INFRASTRUCTURE PARAMETERS                    │
 │    (Working Directory, Structural Type, Environment)    │
 ├────────────────────────────────────────────────────────┤
 │ 🔎 PARSER MODULE CONTEXT (Upstream)                    │
 │    (Metadata Sources, Parsing Results)                 │
 ├────────────────────────────────────────────────────────┤
 │ 🧼 CLEANER MODULE CONTEXT (Upstream)                   │
 │    (Cleaned Dataset Anchors, Handshake Artifacts)      │
 ├────────────────────────────────────────────────────────┤
 │ 🚀 FEATURIZER MODULE CONFIGURATIONS (Active)           │
 │    (Pipeline Orchestration, Logic Routing, Output)     │
 └────────────────────────────────────────────────────────┘
```

---

## 🛠️ Detailed Functional Breakdown (Featurizer Focus)

### 1. Global Infrastructure Parameters
* `working_dir`: The absolute path to the project root. All relative paths are resolved against this anchor by the `PathCoordinator`.
* `structural_type`: Defines the nature of the data (e.g., `cross-sectional`, `longitudinal`).

### 2. Featurizer Module Configurations (`featurizer:`)
This block controls the orchestration of the feature engineering pipeline.

* **Input Anchors**:
    * `featurization_input_data`: Points to the source CSV (typically the output of the Cleaner).
    * `metadata_file`: The KMDS Data Dictionary containing provisional entity tags used for slicing.
* **Logic Routing**:
    * `script_dir`: The directory containing custom transformation functions (e.g., `featurization_scripts`).
    * `script_name`: The primary Python file containing the stage methods (e.g., `featurization.py`).
* **Pipeline Orchestration**:
    * `pipeline`: A sequential list of `StageDefinition` objects. Each stage defines:
        * `name`: A descriptive label for logging.
        * `method`: The exact function name to call in `featurization.py`.
        * `entity`: The KMDS entity tag to filter by (e.g., `geographical`).
        * `sub_filter`: The specific sub-domain (e.g., `Borrower`).
* **Output & Diagnostics**:
    * `featurized_data_file`: The final CSV containing the horizontally concatenated feature matrix.
    * `quarantine_dir`: Destination for records that fail complex logic (e.g., geo-resolution failures).

---

## 📋 Comprehensive Reference Layout Template

Below is the authoritative structured schema syntax for the featurization workspace:

```yaml
# ==============================================================================
# 🌐 GLOBAL INFRASTRUCTURE PARAMETERS
# ==============================================================================
working_dir: "/home/rajiv/programming/dd_parser_cleaner_migration/sba_migration"
structural_type: "cross-sectional"
country_code: "us"

# ==============================================================================
# 🔎 PARSER & CLEANER CONTEXT (Upstream Anchors)
# ==============================================================================
dd_cleaner_output_dir: "dd_cleaner"
metadata_file: "sba_loans_metadata_table.csv"
data_file: "sba_loans_user_cleaned.csv"

# ==============================================================================
# 🚀 FEATURIZER MODULE CONFIGURATIONS
# ==============================================================================

# Logic Discovery
script_dir: "featurization_scripts"
script_name: "featurization.py"

# Input/Output Routing
featurization_input_data: "sba_loans_user_cleaned.csv"
featurized_data_file: "featurized_data.csv"
featurization_output_dir: "featurization"
quarantine_dir: "featurization/quarantine"
feat_doc_directory: "featurization_docs"

# Global Transform Constants
MIN_SUPPORT_THRESHOLD_CAT_VARS: 5

# Pipeline Orchestration (The Waterfall)
pipeline:
  - name: "record_id_generation"
    method: "record_id_definition"
    entity: "System"
    sub_filter: "System"

  - name: "borrower_geo_tagging"
    method: "borrower_geo_tagging"
    entity: "geographical"
    sub_filter: "Borrower"

  - name: "low_count_encoding"
    method: "low_count_featurization_of_cat_vars"
    entity: "categorical"
    sub_filter: "low_count"
    drop_filter:
      - "naicscode"
```

---

## 🎯 Implementation Checklist

1. **Initialization**: Use `initialize_config()` in `featurization_init.py` to generate the baseline file.
2. **Path Resolution**: Ensure `PathCoordinator` properties match the keys defined in the **Featurizer** block.
3. **Waterfall Verification**: Stages must return a DataFrame with a `record_id` index to maintain the survivor universe.

---
*Last Updated: Alignment with SBA Gen 1 Pipeline.*