## 📑 Featurization Path Coordinator Architecture & Routing Contract

The `PathCoordinator` is a core architectural pillar of the `KMDS Featurization` workspace. It acts as a centralized, zero-dependency routing infrastructure contract that isolates all file location mechanics from the featurization engines and stage logic.

---

## 🎯 Why It Exists: The Two Core Constraints

Hardcoding file paths inside data processing components makes pipelines fragile and difficult to maintain. The `PathCoordinator` enforces routing rules to address two primary requirements:

## 1. Common-Sense Standardization

A feature engineering workspace requires predictable, clean boundaries. The coordinator organizes the project layout into distinct, domain-specific subdirectories (`data/`, `featurization_scripts/`, `documents/`). This structured layout keeps the user-cleaned input data (from `dd-cleaner`) isolated from generated feature matrices, audit reports, and quarantine logs.

## 2. "Index-Centric Waterfall" Predictability

The featurization engine is built on an **Index-Centric Waterfall** model, where the integer `record_id` anchors every stage and the output of one transformation dictates the "survivor universe" for the next.

* **The Decoupling**: Featurization stages (e.g., NAICS encoding) are decoupled from the data loading logic. Stages expect the `PathCoordinator` to provide the path to the signed-off metadata table and the user-cleaned dataset, allowing for pure-logic implementations.
* **The Quarantine**: A dedicated routing endpoint handles the isolation of records that fail complex transformations (like geo-tagging), ensuring invalid data is moved to `data/featurization/quarantine/` rather than causing downstream pipeline crashes.
* **The Flow**: The `PipelineRunner` initializes the universe of records. Subsequent stages (like Categorical Encoding) automatically receive a subsetted DataFrame based on the indices returned by previous stages.
* The Rule: To prevent data gaps or manual file-shuffling, the entry and exit points of every pipeline stage must be strictly defined, predictable, and automated.

---

## 🧠 Lifting the Cognitive Burden: Navigate via Properties

By abstracting these pipeline routing constraints, the project achieves a "Context-Blind" architecture for feature engineering.

```text
                ┌──────────────────────────────┐
                │   featurizer_config.yaml     │
                └──────────────┬───────────────┘
                               │ ( authoritative rules )
                               ▼
                ┌──────────────────────────────┐
                │       PathCoordinator        │
                └──────┬───────────────┬───────┘
                       │               │
         ┌─────────────┘               └─────────────┐
         ▼                                           ▼
┌──────────────────┐                       ┌──────────────────┐
│  PipelineRunner  │                       │  Logic Scripts   │
│  (Orchestrator)  │                       │  (featurization) │
└──────────────────┘                       └──────────────────┘
 (reads metadata/data)                       (executes transforms)
```

* Zero User Guesswork: Developers, client scripts, and testing harnesses do not need to track folder nesting patterns or manage complex path strings. They simply pass the target configuration profile once.
* Decoupled Engine Logic: The parser and cleaner modules focus entirely on transformation logic. They request their files directly from the coordinator via clean properties (like `self.paths.data_dictionary_csv_path`, `self.paths.raw_dataset_path`, or the new `self.paths.parser_provisional_report_path`).
* Seamless Environment Shifting: Switching the runtime context from production execution to an isolated testing sandbox (`working_dir="./tests"`) requires zero application code modifications. The coordinator automatically dynamically recalibrates all internal absolute path roots.

---

## 🎯 Workspace Status Check

The featurization routing contract is now finalized and aligned with the SBA Gen 1 pipeline. The `PathCoordinator` is successfully localized in `core` and verified via `test_initialization.py`.

Next, we are ready to implement specific logic stages like Hierarchical NAICS Encoding or validation of the full pipeline execution.
