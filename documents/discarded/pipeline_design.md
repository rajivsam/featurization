# KMDS Featurization Pipeline: Architectural Design & Implementation Guide

## 1. Rationale: The "Skeleton vs. Plugin" Philosophy

The KMDS Featurization system is designed to solve the problem of "Boilerplate Drift." In most data science pipelines, 80% of the code handles I/O, metadata lookup, and data validation, while only 20% contains the actual transformation logic.

This design decouples these concerns into two distinct layers:

1. **The Abstraction (Interface):** Defines *how* data is accessed and prepared based on metadata tags.
2. **The Concrete Implementation (Logic):** Defines *what* transformation is actually performed on the prepared data.

By using this approach, a mid-level engineer can write a complex featurizer (like a Geo-coder) in 15 lines of pure logic, without ever touching file paths or CSV loading code.

---

## 2. Core Components

### 2.1 The PathCoordinator (The Navigator)

The `PathCoordinator` is the single source of truth for the filesystem. It resolves logical keys from the configuration (e.g., `dd_parsing_summary_file`) into absolute paths. No module is permitted to use `os.path.join` manually; they must request the path from the coordinator.

### 2.2 The Featurization Interface (The Abstraction)

Interfaces live under `src/`. They are the "Stage Gatekeepers."
An interface (e.g., `TaggedEntityInterface`) performs the following:

* **Metadata Filtering:** Queries the Data Dictionary for specific tags (e.g., `is_geographical`).
* **Data Slicing:** Extracts only the relevant columns from the main DataFrame.
* **Execution:** Passes the sliced data to the Concrete Implementation.
* **Re-integration:** Merges the engineered features back into the main pipeline context.

### 2.3 The Concrete Implementation (The Logic)

These are standalone Python scripts or functions. They receive a clean, filtered DataFrame and return new features. They are "Context-Blind"—they do not know where the data came from or where it is going.

---

## 3. The Mechanics of a Pipeline Stage

A pipeline is defined in `featurizer_config.yaml` as a sequence of stages. Each stage entry contains:

1. **Interface:** The abstraction to use (e.g., `tabular/tagged_entity`).
2. **Implementation Path:** The path to the custom logic file.
3. **Parameters:** Metadata-specific keys (e.g., "tag": "Geography").

### Runtime Flow:

1. **Orchestrator** reads the stage from the config.
2. **Interface** loads the boilerplate (Metadata + Data).
3. **Interface** dynamically imports the **Implementation**.
4. **Implementation** runs logic on the DataFrame.
5. **Interface** updates the `PipelineRunner` context.

---

## 4. Implementation Example 1: Geographical Entity Featurizer

**Goal:** Automatically compute coordinates for any entity tagged as "Geographic" in the Data Dictionary.

### Step A: The Abstraction (`src/tabular/tagged_entity.py`)

The abstraction handles the "Tag Search."

```python
def tagged_entity_interface(context, implementation_func, tag_name="geography"):
    # 1. Boilerplate: Identify columns with the specific tag
    metadata = context["metadata"]
    target_cols = metadata[metadata["entity_tag"] == tag_name]["column_name"].tolist()
  
    # 2. Slice data
    sub_df = context["data"][target_cols]
  
    # 3. Call Concrete Logic
    new_features = implementation_func(sub_df)
  
    # 4. Integrate
    context["data"] = pd.concat([context["data"], new_features], axis=1)
```

### Step B: The Concrete Implementation (`custom/geo_logic.py`)

```python
def compute_lat_lon(df):
    # Pure logic: assume the input DF has columns like 'city', 'state'
    # returns a new DF with 'lat' and 'lon'
    return some_geo_library.geocode(df)
```

---

## 5. Implementation Example 2: Target Encoder for Categorical Variables

**Goal:** Replace high-cardinality categorical strings with the mean of the target variable.

### Step A: The Abstraction (`src/tabular/categorical.py`)

The abstraction handles "Data Type Discovery."

```python
def categorical_interface(context, implementation_func):
    # 1. Boilerplate: Find all object/category columns
    cat_cols = context["data"].select_dtypes(include=['object']).columns
    target = context["target_column"]
  
    # 2. Call Concrete Logic
    encoded_df = implementation_func(context["data"][cat_cols], context["data"][target])
  
    # 3. Replace columns
    context["data"].update(encoded_df)
```

### Step B: The Concrete Implementation (`custom/encoders.py`)

```python
def target_encode_logic(cat_df, target_series):
    # Pure logic: Calculate means and map them
    for col in cat_df.columns:
        mapping = target_series.groupby(cat_df[col]).mean()
        cat_df[col] = cat_df[col].map(mapping)
    return cat_df
```

---

## 6. How to Add a New Stage

To create a new pipeline stage, a developer follows these three steps:

1. **Identify the Interface:** Does this stage use "Tagged Entities," "Categorical Columns," or "Numerical Columns"? If a new pattern emerges, create a new interface in `src/`.
2. **Write the Logic:** Create a script that takes a DataFrame and returns a DataFrame. Do not include path handling or CSV loading.
3. **Update Config:** Add the stage to the `pipeline_stages` list in the YAML:

```yaml
pipeline_stages:
  - name: "Geo-Coding"
    interface: "tabular/tagged_entity"
    implementation: "custom/geo_logic.py"
    params:
      tag: "Geography"
  - name: "Categorical Encoding"
    interface: "tabular/categorical"
    implementation: "custom/encoders.py"
```

## 7. Summary of Benefits

* **Consistency:** Every "Tagged Entity" featurizer behaves the same way regarding metadata.
* **Testability:** Concrete implementations can be unit-tested with small, mock DataFrames.
* **Discoverability:** The Data Dictionary drives the featurization, ensuring the pipeline stays in sync with the business logic.

---

## 8. Key Integrity Requirement

To maintain a stable and predictable environment, the following three components must maintain **strict variable naming consistency**:

1. **`featurization_init.py`**: The bootstrap logic that generates the configuration.
2. **`featurization_config.yaml`**: The authoritative single source of truth.
3. **`path_coordinator.py`**: The interface that resolves these variables into system paths.

**The Rule**: Every system variable (e.g., `featurization_input_data`, `dd_cleaner_output_dir`, `metadata_file`) must be named identically across these three files. If `init` creates a key that the `PathCoordinator` does not recognize, or if a manual edit to the YAML breaks this naming contract, the pipeline will fail to resolve absolute paths.

```
<!--
[PROMPT_SUGGESTION]Let's define the base class or functional signature for the 'tagged_entity' abstraction.[/PROMPT_SUGGESTION]
[PROMPT_SUGGESTION]How should the featurization_config.yaml structure look to support this mapping of Interfaces to Concrete Paths?[/PROMPT_SUGGESTION]
```
