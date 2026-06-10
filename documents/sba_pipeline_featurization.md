# SBA Featurization Pipeline: End-to-End Stage Specification

## 1. Architecture Summary
The SBA pipeline uses an index-centric waterfall contract.

- Universal anchor: `record_id` index.
- Stage signature: `method(context, stage_cfg) -> DataFrame`.
- Default index rule: each stage returns a subset of current survivor rows.
- Merge rule: stage outputs are concatenated horizontally by index.
- Controlled exception: final merge stage may re-introduce active rows using `allow_new_indices: true`.

Core intent:
- Modeling development is performed on non-active rows (`loan_status_r` in `{0, 1}`).
- Active rows (`loan_status_r = -1`) are held out, transformed with train-fitted artifacts, then merged back in an aligned feature space.

---

## 2. Configuration Anchors
Key fields in `featurizer_config.yaml`:

- `MIN_SUPPORT_THRESHOLD_CAT_VARS`: support threshold for low-count handling.
- `VALIDATION_SIZE`: train/validation split fraction.
- `FEATURE_SELECTION_MIN_NON_NULL_RATE`: minimum train non-null rate for feature retention.

Important file/path anchors:
- Input data: `data/dd_cleaner/sba_loans_user_cleaned.csv`
- Metadata: `data/dd_cleaner/sba_loans_metadata_table.csv`
- User stage logic: `featurization_scripts/featurization.py`

---

## 3. Stage Sequence (Canonical)

### Stage 1: `record_id_definition`
Creates `record_id` when absent and promotes it to index.

### Stage 2: `borrower_geo_coding`
Adds `borrower_latitude` and `borrower_longitude` using fallback:
- ZIP -> CITY -> STATE centroid.

### Stage 3: `low_count_featurization_of_cat_vars`
Two-pass categorical low-count handling for general categoricals:
- pass 1: low-support levels recoded to `OTHERS`
- pass 2: sequential support enforcement with in-stage row drops
- output suffix: `_rcs`

### Stage 4: `hierarchical_low_count_var_encoding`
NAICS-specific hierarchical support recoding.
- Uses right-side masking (NAICS-aligned).
- Example: `722511 -> 72251* -> 7225** -> ...`
- Output column: `naicscode_rcs`

### Stage 5: `loan_status_recoding`
Maps operational status labels to:
- active: `-1`
- closed: `0`
- distressed: `1`

### Stage 6: `filter_modeling_universe`
Filters out active rows from modeling path.
- Keeps active rows in `context["active_holdout"]` for later scoring/reconciliation.
- Survivor universe becomes only rows with target in `{0, 1}`.

### Stage 7: `stratified_train_val_split`
Adds split flag on modeling universe:
- `dataset_split` in `{train, val}`
- stratified by `loan_status_r`
- controlled by `VALIDATION_SIZE`

### Stage 8: `target_encode_categorical_vars`
Leakage-safe target encoding:
- fit `TargetEncoder` on train rows only
- transform modeling universe (train + val)
- transform active holdout with same train-fitted encoder
- stores reusable artifacts in context:
  - `target_encoder`
  - `target_encoder_cols`
  - `active_encoded`

### Stage 9: `harmonize_and_project_feature_space`
Builds canonical feature schema from train partition and projects both modeled and active partitions.
- candidate pool includes encoded and numeric feature columns
- selected by train-based thresholds:
  - min non-null rate (`FEATURE_SELECTION_MIN_NON_NULL_RATE`)
  - min unique count (`min_unique` stage arg)
- stores:
  - `selected_features`
  - `modeled_projected`
  - `active_projected`
- adds partition marker:
  - `dataset_partition = modeled` for train/val rows
  - `dataset_partition = active` for active holdout rows

### Stage 10: `merge_modeled_and_active_partitions`
Concatenates projected modeled and active partitions into one aligned dataset.
- Requires `allow_new_indices: true` because active indices are reintroduced.
- Final persisted artifact contains all partitions with shared feature schema.

---

## 4. Artifact and Leakage Rules

### Fit-on-train-only rule
The following are fit only on train rows and reused elsewhere:
- target encoder
- feature subset/schema

### Transform-only rule for validation and active
Validation and active partitions are transformed using train-fitted artifacts.
No refit is performed on validation or active data.

### Merge reconciliation rule
Row counts may differ by partition, but feature columns must match exactly before merge.
Projection enforces a fixed schema based on train-selected features.

---

## 5. Output Semantics
Final persisted output (`featurized_data.csv`) includes:
- engineered feature columns
- target column (`loan_status_r`)
- split marker (`dataset_split`: `train`, `val`, `active`)
- partition marker (`dataset_partition`: `modeled`, `active`)

Interpretation:
- `dataset_partition = modeled` rows are development rows (train/val).
- `dataset_partition = active` rows are active holdout rows transformed into the same feature space.

---

## 6. Modular Code Locations

Package-side reusable modules:
- `src/tabular/low_count_cat_var_encoding.py`
- `src/tabular/hierarchical_low_count_var_encoding.py`
- `src/tabular/modeling_filter.py`
- `src/tabular/train_val_split.py`
- `src/tabular/target_encoding.py`
- `src/tabular/feature_space.py`

User-stage orchestration wrapper:
- `featurization_scripts/featurization.py`

Runner/core behavior:
- `src/featurization/core/sequential_pipeline_runner.py`
- `src/featurization/core/path_coordinator.py`
- `src/featurization/core/featurization_init.py`

---

## 7. Validation Coverage
Primary smoke/integration test:
- `tests/test_sba_pipeline.py`

Test checks include:
- canonical pipeline method presence
- expected engineered columns
- binary modeled target universe
- split and partition markers
- persisted output file contains required columns

---

## 8. Design Notes
- Keep NAICS hierarchy handling separate from generic low-count categorical handling.
- Keep active scoring/reconciliation separate from model fitting stages.
- Keep stage wrappers thin and delegate reusable logic to package modules.
- Prefer explicit stages over overloaded parameterization when readability is at risk.

## 9. Current Scope Boundary
- This session stops at producing the model-ready numeric dataset after feature projection/selection.
- Current feature selection is threshold-based (train non-null rate + uniqueness), not model-based.
- Active rows are encoded/projected into the same selected feature space and merged for downstream scoring.

Planned enhancement (next phase):
- Add model-based feature selection (e.g., XGBoost or Random Forest wrapper) fit on train only.
- Persist selected feature list from model-based selector and reuse it for val and active projection.
- Keep leakage controls unchanged: fit on train only, transform/project on val and active.
