# SBA Featurization Pipeline: Stage Specifications

## Core Architecture: The Waterfall Model
The pipeline is built on an **Index-Centric Waterfall** model. A key principle of this design is that **filtration is done by each stage**, ensuring that each subsequent stage only receives the survivors from all preceding steps. This ensures the data universe is progressively refined and prevents redundant processing of records that failed earlier stages.

---

## 1. Foundational Stage: Record ID Generation

### Overview
The `Record ID Generation` stage establishes the primary anchor for the entire pipeline. It ensures that every row in the dataset has a unique, stable identifier (`record_id`) which is then promoted to the DataFrame index. This index is used by the `PipelineRunner` to perform horizontal concatenation and maintain the "survivor universe" across stages.

### Configuration Requirements
To include this stage in the pipeline, add an entry to the `pipeline` list in `featurizer_config.yaml`:

```yaml
pipeline:
  - name: "Record ID Generation"
    method: "record_id_definition"
    entity: "System"
    sub_filter: "System"
```

### Technical Implementation Details
1. **Identifier Check**: The method checks the input `context['data']` for an existing `record_id` column.
2. **Sequence Generation**: If the column is missing, it generates a clean integer sequence matching the length of the input data.
3. **Index Promotion**: While the method returns a DataFrame containing the `record_id` column, the `PipelineRunner` specifically looks for this column name. When detected, the runner:
    * Sets `record_id` as the index for the stage result.
    * Re-indexes the master `context['data']` to use this new index.
    * Ensures all subsequent stages are aligned to this specific index.

### Output Schema
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `record_id` | Integer | (Promoted to Index) The unique identifier for the loan record. |

### Logic Location
- **Stage Method**: `/featurization_scripts/featurization.py`

---

## 2. Feature Stage: Borrower Geo Coding

## Overview
The `Borrower Geo Coding` stage converts geographical attributes (City, State, Zip) associated with a Borrower into Latitude and Longitude coordinates. This is performed using a combination of postal code lookups and address string geocoding.

## Configuration Requirements
To include this stage in the pipeline, add an entry to the `pipeline` list in `featurizer_config.yaml` with the following keys:

- **`name`**: Descriptive name (e.g., `Borrower Geo Coding`).
- **`method`**: Must be `borrower_geo_coding`.
- **`entity`**: Set to `geographical`. This tag is used to filter metadata for attributes where the category flag (e.g., `is_geographical`) is true.
- **`sub_filter`**: Set to `Borrower`. This matches the `provisional_entity_assignment` value in the metadata.

### Example Configuration
```yaml
pipeline:
  - name: "Borrower Geo Coding"
    method: "borrower_geo_coding"
    entity: "geographical"
    sub_filter: "Borrower"
```

## Technical Implementation Details

### 1. Attribute Discovery
The method uses `get_stage_subset(context, entity, sub_filter)` to isolate the relevant columns. It specifically looks for columns in the input data where the KMDS metadata has:
- `is_geographical` (or `is_geographic`) set to `True`.
- `provisional_entity_assignment` set to `Borrower`.

### 2. Coordinate Transformation
The transformation logic is delegated to `compute_geo_coordinates`:
- **Zip Lookup**: Attempts to resolve coordinates via `pgeocode` using the identified Zip code column.
- **Address Geocoding**: For records not resolved by Zip, it builds an address string from the subsetted columns and queries `Nominatim`. 
- **Caching**: Address queries are cached to optimize performance for repeated locations.

### 3. Output Requirements
The stage is designed to be a "Feature Producer." It performs the following clean-up before returning:
- **Renaming**: Derived coordinates are renamed from internal proxy names to `borrower_latitude` and `borrower_longitude`.
- **Subsetting**: Returns only the two coordinate columns.
- **Index Alignment**: The resulting DataFrame maintains the original index (e.g., `record_id`) to ensure the `PipelineRunner` can horizontally concatenate the features back to the main dataset.

## Output Schema
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `borrower_latitude` | Float | Derived latitude coordinate. |
| `borrower_longitude` | Float | Derived longitude coordinate. |

## Logic Location
- **Stage Method**: `/featurization_scripts/featurization.py`
- **Transformation Engine**: `src/featurization/transforms/geo.py`

---

## 3. Feature Stage: Low Count Categorical Encoding

### Overview
The `Low Count Categorical Encoding` stage processes categorical variables to reduce noise and handle high-cardinality columns. It identifies "rare" levels (those appearing fewer times than a defined threshold) and attempts to consolidate them into a single `OTHERS` category.

### Configuration Requirements
```yaml
pipeline:
  - name: "Low Count Categorical Encoding"
    method: "low_count_featurization_of_cat_vars"
    entity: "categorical"
    sub_filter: "low_count"
    drop_filter: ["loanstatus", "naicscode"]
```

### Technical Implementation Details
1. **Attribute Discovery**: Uses `get_categorical_subset(context, drop_filter)` to identify columns that are categorized as 'object' or 'category' in Pandas and are present in the KMDS metadata.
2. **Support Thresholding**: Reads `MIN_SUPPORT_THRESHOLD_CAT_VARS` from the configuration (defaults to 5).
3. **Consolidation Logic**:
    * **Pass 1: Roll Up**: Each categorical column is scanned. Levels appearing fewer times than the threshold are mapped to the `'OTHERS'` category in a temporary DataFrame.
    * **Pass 2: Support Check**: The system iterates through the rolled-up columns. It calculates the frequency of `'OTHERS'` within the *current* survivor population.
    * **Sequential Waterfall**: If the `'OTHERS'` count for an attribute is non-zero but less than the threshold, those specific records are dropped immediately. 
    * **Subsequent Recalculation**: Because drops are sequential, the support for `'OTHERS'` in the *next* attribute is evaluated only against the remaining records.
    * **Logging**: The system reports the names of attributes that triggered insufficient support drops and the total count of removed records.
4. **Column Naming**: The resulting columns are suffixed with `_encoded`.

### Output Schema
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `[original_name]_encoded` | String/Object | The categorical column with rare levels consolidated or dropped. |

### Logic Location
- **Stage Method**: `/featurization_scripts/featurization.py`
- **Attribute Discovery**: `src/tabular/low_count_cat_var_encoding.py`