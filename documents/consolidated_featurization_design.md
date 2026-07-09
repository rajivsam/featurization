# Consolidated Design Document: KMDS Featurization Service

## 1. Overview

The **KMDS Featurization Service** is a modular, config‑driven pipeline that transforms raw datasets into model‑ready features. It supports cross‑sectional, survival analysis, and SBA workflows, integrates categorical and text encoding best practices, and enforces leakage‑safe transformations. Outputs are standardized CSV artifacts ready for downstream modeling.

---

## 2. Core Architecture

* **Stage‑based pipeline** : Each stage follows the contract `method(context, stage_cfg) -> DataFrame`.
* **Config‑driven orchestration** : `featurizer_config.yaml` defines stage order, path routing, and tunables.
* **PathCoordinator** : centralizes path resolution and runtime parameters, eliminating hidden assumptions.
* **Outputs** :
  * `featurized_data.csv`: engineered features + metadata columns.
  * `model_ready_numeric_data.csv`: numeric/bool only, model‑ready export.

---

## 3. Pipeline Variants

### Cross‑Sectional Pipeline

* Record ID definition.
* Categorical/numerical prep.
* Low‑count categorical encoding.
* Hierarchical encoding.
* Target encoding.
* Feature selection.
* Merge operations.

### Survival Pipeline

* Transforms event logs or interval long‑form datasets into survival‑ready wide form.
* Produces duration/event fields per subject.

### SBA Pipeline

* Index‑centric waterfall contract.
* Stages: record ID definition, borrower geo coding, categorical/numerical prep, low‑count/hierarchical encoding, target encoding, feature selection, merge modeled and active partitions.

---

## 4. Feature Advisor Service

* Provides **model‑aware recommendations** for featurization.
* Supports **cross‑sectional** and **temporal** datasets.
* For temporal datasets, recommends survival pipeline transformation before applying cross‑sectional logic.
* Produces CSV and Markdown recommendation artifacts.

---

## 5. Encoding Guidelines

### Categorical Encoding

* Low‑count categories → frequency thresholding (`OTHER`).
* Hierarchical long tails → hierarchical aggregation.
* High‑cardinality with continuous target → smoothed target encoding.
* Guardrails: leakage‑safe (fit on train only, immutable for val/active).

### Text Encoding

* Short text → TF‑IDF n‑grams.
* Long‑form text → pre‑trained embeddings (sentence‑transformers).
* Tree ensembles → native text handlers (CatBoost, LightGBM).

### Non‑Numeric Attributes

* LLM‑based advisor recommends optimal encoding strategies based on metadata and model intent.

---

## 6. Guardrails

* **Leakage control** : stateful transformations fit only on train; applied immutably to val/active.
* **Artifact rules** : target encoders, feature‑selection models fit on train only.
* **Merge reconciliation** : partitions may differ in row counts but must align on feature columns.
* **Validation coverage** : tests check stage methods, engineered columns, split/partition markers, and persisted outputs.

---

## 7. Configuration Model

* **featurizer_config.yaml** is the single runtime source of truth.
* Anchors: `metadata_file`, `featurization_input_data`, `featurized_data_file`, `model_ready_data_file`.
* Modeling constants: `MIN_SUPPORT_THRESHOLD_CAT_VARS`, `VALIDATION_SIZE`, `FEATURE_SELECTION_MIN_NON_NULL_RATE`, `MODEL_READY_NUMERIC_ONLY`.
* Tree‑based feature selection keys: `FEATURE_SELECTION_METHOD`, `FEATURE_SELECTION_TOP_K`, `FEATURE_SELECTION_TREE_MODEL`.

---

## 8. Developer Guidance

* Keep stage wrappers thin; reusable transformations live in `src/tabular/`.
* New tunables must be wired in three places: `featurizer_config.yaml`, `PathCoordinator`, `featurization_init.py`.
* Use notebook utilities (`notebook_utils_usage.md`) to resolve and load artifacts in Jupyter workflows.

---

## 9. Testing Strategy

* **Unit tests** : validate stage methods and engineered columns.
* **Integration tests** : simulate full pipeline runs with representative datasets.
* **Fixtures** : include canonical CSVs for cross‑sectional, survival, SBA pipelines.
* **Validation criteria** : outputs match schema, leakage guardrails enforced, handshake respected.

---

## 10. Observability

* Structured logs for stage execution, feature counts, and validation errors.
* Metrics: number of features generated, blocked featurizations, common validation failures.
* Diagnostics: prioritized remediation list with severity, remediation steps, and sample rows.

---

## 11. Acceptance Criteria

* Parser emits manifests matching JSON Schema.
* Cleaner validates and writes handshake with correct `status`.
* Featurizer consumes handshake and refuses to proceed if `status == blocked`.
* Outputs are reproducible, leakage‑safe, and model‑ready.

---

## 12. Summary

The KMDS Featurization Service is a **config‑driven, leakage‑safe, stage‑based pipeline** supporting multiple dataset archetypes. It integrates categorical/text encoding best practices, model‑aware feature advisor logic, and centralized path/config resolution. Outputs are standardized CSVs ready for modeling, with strong guardrails against leakage and reproducibility issues.
