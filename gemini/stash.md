---
## 🗃️ KMDS Featurization Package: Context Pick-Up Stash

## 📦 Package Identity & Environment

* Package Name: `featurization` (supporting the `kmds-data-helper` ecosystem).
* Build System: `hatchling` (configured inside `pyproject.toml`).
* Environment Manager: `uv` (installed dependencies: `pandas`, `numpy`, `scikit-learn`, `geopy`, `pgeocode`, `pyyaml`).
* CLI Command Entry Point: `compute-features --working-dir <path> --target-col <col>` mapped directly to `src/featurization/cli.py:main`.
---
## 📂 Active Workspace Paths & Configurations

The active configuration is saved at `/home/rajiv/programming/featurization/config.yaml`:

```yaml
dd_parsing_output_dir: "dd_analysis_results"
dd_parsing_summary_file: "sba_analysis_results.csv"
dd_cleaner_output_dir: "dd_cleaner_results"
cleaned_file_from_dd_cleaner: "feature_selection_ready.csv"
featurization_output_dir: "featurization"
featurization_output_file: "featurized_data.csv"
feat_doc_directory: "featurization_docs"
entity_assignment_output: "entity_assignments.md"
exclude_attributes: ["internal_row_id", "legacy_status_code"]
exclude_regex: "(_at|_dt|date|time|timestamp)"
importance_threshold: 0.05
country_code: "us"
```

* Active Testing Target Directory: `/home/rajiv/programming/kmds_descriptive_analytics/kmds_sba_loans`

---

## 🛠️ Current Code State (Verified & Working)

1. `src/featurization/transforms/filters.py`: Contains `exclusion_filter()`. Successfully uses explicit lists and regular expressions to clean incoming datasets.
2. `src/featurization/engine.py`: Contains `FeaturizationService`.

   * Successfully resolves dynamic runtime paths.
   * Drops implicit datetime attributes (verified on 5 fields: `paidinfulldate`, `approvaldate`, `firstdisbursementdate`, `chargeoffdate`, `asofdate`).
   * Parsed the custom `# DD-PARSER-SIGNATURE: PROCESSED-BY-LLAMA3.2` CSV structure smoothly.
   * Safely captures unmapped attributes into `Unassigned_Entity`.
   * Automatically exports a KMDS-compliant Markdown assignment matrix to `documents/featurization_docs/entity_assignments.md`.

---

## 🎯 Discovered Entity Groups (Input for Next Task)

The last test run successfully mapped out the following geographical column profiles:

* `Bank`: `['BankStreet', 'BankCity', 'BankState', 'BankZip']`
* `Borrower`: `['BorrStreet', 'BorrCity', 'BorrZip']`
* `Project`: `['ProjectCounty', 'ProjectState']`
* `SBA`: `['SBADistrictOffice']`
* `Unassigned_Entity`: `['LocationID', 'BankFDICNumber', 'NaicsCode', 'NaicsDescription', 'FranchiseName', 'CongressionalDistrict']`

---

## 🚀 Next Session Action Items

When resuming, we will focus entirely on implementing Proxy-First Geo-Gating in `src/featurization/transforms/geo.py`:

1. Address Composition Strategy: Determine how to programmatically combine fields (e.g., merging `BorrStreet` + `BorrCity` + `BorrZip` into a unified lookup string) for `geopy` (Nominatim) or fallback directly to `pgeocode` for zipcode-only extractions.
2. Coordinate Generation Execution: Build the loops to generate one pair of proxy latitude/longitude fields for each valid entity group.
3. Feature Selection Gate: Build the `scikit-learn` `RandomForestRegressor` baseline to measure feature importance against the user-specified `--target-col` and apply the `importance_threshold` gate.
