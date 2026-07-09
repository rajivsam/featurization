# Feature Advisor Service

The package contains a feature advisor service that generates actionable featurization recommendations.
It supports **two dataset archetypes**: cross-sectional and temporal.

---

## Dataset Type Selection

When invoked, the advisor first asks the user to classify the dataset:

- **Cross-sectional dataset**: snapshot tables, one row per subject, no explicit time axis.
- **Temporal dataset**: time-indexed data, multiple rows per subject (event logs or intervallic long form).

---

## Cross-sectional Component

For cross-sectional datasets, the advisor generates recommendations from:

- the metadata table (`resolver.metadata_path`)
- the input dataset (`resolver.featurization_input_path`)
- explicit downstream model intent (`model_intent`)

### Value Proposition

- Offers metadata-driven guidance rather than generic type rules
- Prefers native categorical handling for `catboost`, `xgboost`, and `lightgbm`
- Falls back to explicit encoder recommendations for non-GBDT modeling targets
- Produces CSV and Markdown recommendation artifacts for review

---

## Temporal Component

For temporal datasets, the advisor recommends using the **survival analysis pipeline** to convert raw data into a longitudinal summary form:

- **Event Log input**: multiple chronological transaction rows per subject.
- **Intervallic Long Form input**: multiple rows per subject representing stable time intervals.
- **Output (Structural Summary Wide Form)**: one row per subject, with explicit duration and event fields, plus flattened covariates.

Once transformed into wide form, the **cross-sectional advisor logic applies** to the resulting dataset, ensuring consistent featurization recommendations.

---

## How to Use

From the CLI:

```bash
featurization-cli advise --working-dir /path/to/workspace --model-intent catboost
```
