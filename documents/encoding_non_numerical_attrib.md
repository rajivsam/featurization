# Design Document: LLM-Based Encoding Recommendations for Non-Numeric Attributes

## 1. Objective

To provide an automated, LLM-driven advisory service that analyzes dataset metadata and recommends optimal featurization strategies for categorical and text attributes. These recommendations are grounded in the project's core guidelines: `categorical_var_encoder_guidelines.md` and `text_attribute_featurization.md`.

## 2. Input Requirements

The recommendation engine requires three primary inputs:

1. **Metadata Table**: Specifically the `logical_type` and `physical_type` for every attribute (e.g., from `sba_loans_metadata_table.csv`).
2. **Architectural Guidelines**: The raw text content of the categorical and text featurization markdown files to serve as "Ground Truth" for the LLM.
3. **User Intent (Model Type)**: A parameter indicating the target downstream model (e.g., `catboost`, `xgboost`, `lightgbm`, or `linear_model`).
    *   **Why this is required**: This selection fundamentally dictates whether features need explicit manual encoding or should be passed raw to the model.
    *   **Native Handling**: Modern GBDT implementations like **CatBoost**, **LightGBM**, and **XGBoost** have built-in encoding models (e.g., CatBoost's Ordered Target Encoding). If these are selected, the advisor should frequently recommend "Native Handling" to leverage optimized C++ kernels and built-in leakage protection, rather than applying manual Python-based encoders.
    *   **Explicit Encoding**: For "classic" models (e.g., Linear Regression, Neural Networks), explicit numerical encoding (One-Hot, Target, etc.) is mandatory as these models cannot process non-numeric data natively.
    *   **Assistant Guidance**: This allows the advisor to distinguish between "Required Featurization" and "Native Model Delegation."

## 3. System Architecture

### 3.1 LLM Prompt Construction

The system will generate a context-rich prompt for the LLM (e.g., Gemini or GPT-4) structured as follows:

* **Role**: Senior Feature Engineering Architect.
* **Context Injection**: The full content of `categorical_var_encoder_guidelines.md` and `text_attribute_featurization.md`.
* **Task**: "Evaluate the following attributes from our metadata table. For each attribute, recommend the most robust featurization method that minimizes leakage and maximizes predictive signal, adhering strictly to the provided guidelines. Account for the user's intent to use [MODEL_TYPE]."
* **Format Constraint**: Return a structured JSON array suitable for conversion into a Pandas DataFrame.

### 3.2 Decision Logic (Embedded in Guidelines)

The LLM will be instructed to follow these routing rules, prioritizing native capabilities where they exist:


| Attribute Type  | Condition                       | Recommendation                                                                      |
| :---------------- | :-------------------------------- | :------------------------------------------------------------------------------------ |
| **Categorical** | User Intent in `[catboost, xgboost, lightgbm]` | **Native Model Handling**. Pass raw categories to the model's internal encoder. |
| **Categorical** | High Cardinality / GBDT=False   | `low_count_cat_var_encoding` followed by `target_encoding`.                         |
| **Categorical** | Hierarchical (e.g., NAICS, Geo) | `hierarchical_low_count_var_encoding` via right-side masking.                     |
| **Text**        | Short / Keyword-based           | `TF-IDF` + `TruncatedSVD` (Dense Projection) to manage sparsity.                    |
| **Text**        | Long-form / Unstructured        | `Sentence Transformers` (e.g., `all-MiniLM-L6-v2`) for semantic embeddings.         |

## 4. Implementation Details

### 4.1 Output Schema

The tool will produce a DataFrame with the following columns:


| Column               | Description                                                                                                                                             |
| :--------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `attribute`          | The name of the feature from the metadata table.                                                                                                        |
| `recommended_method` | The specific pipeline stage or module name to use.                                                                                                      |
| `rationale`          | A detailed explanation of why this method was chosen, citing specific rules from the guidelines (e.g., "To prevent sparsity issues in tree models..."). |

### 4.2 Class Blueprint: `EncodingAdvisor`

A new analysis utility will be implemented in `src/analysis/encoding_advisor.py`.

```python
class EncodingAdvisor:
    def __init__(self, metadata_path, model_intent="gbm"):
        self.metadata = pd.read_csv(metadata_path)
        self.intent = model_intent
      
    def _load_guidelines(self):
        # Reads categorical_var_encoder_guidelines.md and text_attribute_featurization.md
        pass

    def get_recommendations(self) -> pd.DataFrame:
        """
        Filters metadata for non-numeric columns, constructs the LLM prompt, 
        and parses the result into the (attribute, recommended_method, rationale) format.
        """
        pass
```

## 5. Integration with Workspace

This advisor will be exposed as a diagnostic tool.

1. **CLI**: `featurization-cli advise --metadata sba_metadata.csv --intent catboost`
2. **Output**: Generates a CSV or updates the `entity_assignments.md` to help the user configure the `pipeline` section of `featurizer_config.yaml`.

## 6. Safety & Guardrails

* **Leakage Check**: The rationale must explicitly state how the recommended method handles the Train/Val split (e.g., "Fitted on Train, Transformed on Val").
* **Native Preference**: If a GBDT intent is provided, the advisor should prioritize native handling over manual `TargetEncoder` or `OneHotEncoder` to leverage optimized internal algorithms (like CatBoost's Ordered TS or LightGBM's histogram-based splits).
* **Complexity Management**: For text, the advisor must recommend dimensionality reduction (SVD) if the target model is a GBM (XGBoost/LightGBM) to prevent performance degradation from sparse features.

## 7. Example Output Data


| attribute   | recommended_method                    | rationale                                                                                                                                                |
| :------------ | :-------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `borr_zip`  | `low_count_cat_var_encoding`          | High cardinality detected. Per guidelines, we must group rare ZIP codes into 'OTHER' before encoding to prevent overfitting.                             |
| `loan_desc` | `SentenceTransformer`                 | Long-form text. Pre-trained embeddings capture semantic context better than keyword-based TF-IDF.                                                        |
| `naicscode` | `hierarchical_low_count_var_encoding` | This is a hierarchical industry code. Right-side masking allows us to preserve sector-level information even for rare sub-industries.                    |
| `city`      | `Native CatBoost Handling`            | User is using CatBoost. Manual encoding is redundant as CatBoost handles high-cardinality strings natively using its proprietary leakage-safe algorithm. |

```

I have initialized this design based on your requirement for a consultative, metadata-driven approach. It bridges the gap between your data's physical structure and the architectural best practices you've defined in the repository.

<!--
[PROMPT_SUGGESTION]Implement the EncodingAdvisor class in src/analysis/encoding_advisor.py based on this design document.[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]Create a mock metadata CSV and run a test case for the EncodingAdvisor to see the LLM's rationale for NAICS codes.[/PROMPT_SUGGESTION]
```
