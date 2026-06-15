------------------------------
## 📑 Categorical Encoding Architecture & Best Practices Guide## 1. Core Integration Context (rajivsam/featurization)
This document defines the architectural standards for categorical feature engineering within the featurization pipeline framework. Categorical transformations are isolated as discrete column-selection components inside the reusable tabular directory:

* src/tabular/low_count_cat_var_encoding.py
* src/tabular/hierarchical_low_count_var_encoding.py
* src/tabular/target_encoding.py

## The Runtime Guardrail
All encoding components must conform strictly to the package's leakage-safe modeling flow: stateful transformations (e.g., target means, frequency maps, vocabulary indices) are computed strictly during the train partition split step and applied immutably to val and active partitions.
------------------------------
## 2. Taxonomy & Module Routing Matrix
Before declaring an orchestration block in featurizer_config.yaml, ensure features are correctly mapped to their corresponding functional modules:

| Feature Taxonomy & Distribution | Module Route | Preferred Approach | Runtime Advantage |
|---|---|---|---|
| High Support for Most / Low Support for Few | src/tabular/low_count_cat_var_encoding.py | Conventional "OTHER" (Frequency Thresholding) | Isolates tail noise; safeguards high-support signals from hash collisions. |
| Multi-Level/Geographic Long Tails | src/tabular/hierarchical_low_count_var_encoding.py | Hierarchical Aggregation | Grouping rare items step-wise by parent dependencies (e.g., Zip → City → State). |
| Clean Strings with Continuous Target Relationships | src/tabular/target_encoding.py | Smoothed M-Estimate / Out-of-Fold Target Encoding | Translates high-cardinality values directly into an informative, model-ready numeric scalar. |
| Infinite/Uncapped Cardinality Scaling | External Custom Integration | Feature Hashing (The Hashing Trick) | Binds memory footprints to a fixed $2^N$ bit vector; bypasses vocabulary dictionaries. |

------------------------------
## 3. Detailed Architectural Blueprint: The "Clean Bucket" Policy
Handling unseen Out-of-Vocabulary (OOV) data during streaming, validation, or active scoring requires a deterministic, zero-crash routing policy.

                [Incoming Row Validation (val/active)]
                                │
                                ▼
         Does 'record_id' feature exist in Training Map?
               ├──► YES ──► Retrieve learned numeric encoding
               │
               └──► NO  ──► Intercept and rewrite feature as '<UNKNOWN>' / 'OTHER'

## ⚙️ Step-by-Step Implementation Mechanics

   1. The Train-Set Frequency Bound: During execution on the training partition, the module calculates the absolute value counts for each categorical target. Any category failing to meet the MIN_CATEGORY_SUPPORT_THRESHOLD (e.g., < 2% of training rows or an absolute count < 50) is stripped of its unique identifier.
   2. Isolating the Noise: All sub-threshold strings are compressed into a unified string literal token: 'OTHER'.
   3. The OOV Interface Contract: The encoder pipeline reserves state index 0 or an explicit string value <UNKNOWN> inside its serialization parameters.
   4. Transformation Enforcement: When transforming val or active files, any category completely absent from the initial train-fitted vocabulary maps directly to the designated unknown state index instead of throwing an out-of-bounds KeyError.

------------------------------
## 4. Framework Reference Implementations## 4.1 Production Pipeline Syntax (Feature-Engine)
When standard Scikit-Learn transformers are desired for your tabular modules, Feature-engine offers clean validation boundary safety and handles rare-label merging seamlessly.

import pandas as pdfrom feature_engine.encoding import RareLabelEncoder, MEstimateEncoderfrom sklearn.pipeline import Pipeline
def transform_low_count_features(df_train: pd.DataFrame, df_val: pd.DataFrame, target_col: str):
    """
    Example implementation aligning with the train-fit/val-transform contract.
    Ensures that rare labels are consolidated before numeric target mappings are calculated.
    """
    # 1. Isolate target and predictors
    X_train = df_train.drop(columns=[target_col])
    y_train = df_train[target_col]
    
    # 2. Define the Pipeline
    cat_pipeline = Pipeline([
        ('rare_grouper', RareLabelEncoder(
            tol=0.02,             # Group classes representing < 2% of the train data
            n_categories=5,       # Only apply if column contains >= 5 unique categories
            replace_with='OTHER'  # Enforce standardized bucket token
        )),
        ('m_estimate_encoder', MEstimateEncoder(
            m=10.0                # Smoothing factor handling low-support variance
        ))
    ])
    
    # 3. Fit strictly on train partition
    cat_pipeline.fit(X_train, y_train)
    
    # 4. Transform partitions independently using train-fitted parameters
    X_train_encoded = cat_pipeline.transform(X_train)
    X_val_encoded = cat_pipeline.transform(df_val.drop(columns=[target_col]))
    
    return X_train_encoded, X_val_encoded

## 4.2 Native Multi-Category Trees (CatBoost & LightGBM)
If the downstream stage passes data into a Gradient Boosted Decision Tree (GBDT) framework, avoid manually encoding features via standalone Python libraries. Over-allocating one-hot encoders or basic target tools outside the core engine slows down memory optimization and causes target leakage.

* CatBoost Integration: Direct raw categorical string tables directly to the backend. CatBoost utilizes an advanced Ordered Target Encoding method in its C++ layer. It calculates target parameters sequentially across random data history shuffles, eliminating cross-validation leakage out of the box.
* LightGBM Integration: Map strings to ordinal integers inside your preprocessing stages. LightGBM then processes categories directly by sorting their histograms according to target orientation, computing highly optimized multi-category splits dynamically at every tree node.

------------------------------
## 5. Security Guardrails & Data Auditing Constraints

* The Golden Rule of State Seeding: The state parameters—including target counts, global target averages, variance modifiers, and vocabulary indices—must be extracted only from rows marked as the training group.
* Immutable Inference Pipelines: All encoding schemas are frozen post-extraction. Dynamically modifying dictionary parameters or recalculating averages based on incoming evaluation patterns causes Data Distribution Leakage, which completely invalidates model validation.
* The Collision Conundrum of Feature Hashing: Avoid applying feature hashing blindly if your data exhibits a massive power-law distribution (a few dominant categories paired with a massive long tail). If a valuable, high-support category inadvertently shares a hashed bin with a volatile, low-support noise category due to a hash collision, its clean signal will be diluted, leading to an unpredictable drop-off in model accuracy.

------------------------------
To help complete the integration into your codebase, let me know:

* Do you want a boilerplate YAML template showing how to declare these parameters inside your featurizer_config.yaml?
* Would you like an automated pytest module design for tests/ to verify that your encoders handle novel categories without crashing the runner?


