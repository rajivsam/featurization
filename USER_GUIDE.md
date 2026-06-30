# 📖 User Guide: KMDS Featurization

## 📑 Overview
KMDS Featurization turns cleaned tabular data into model-ready datasets using a configurable, leakage-safe stage pipeline. It is built for:
- cross-sectional feature engineering workflows
- optional survival analysis workflows
- metadata-driven configuration and reproducible workspace paths

## 🚀 Core workflow
1. **Initialize** a workspace config
2. **Bootstrap** a starter pipeline configuration
3. **Run** the featurization pipeline
4. **Review** the output artifacts and diagnostics

## 🔧 Install
Use your Python environment to install from source or package.

```bash
pip install -e .
```

## 🚀 Quick start

### 1. Initialize workspace configuration
```bash
featurization-cli init \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv
```

### 2. Bootstrap a starter config
```bash
featurization-cli bootstrap \
  --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_dataset.csv
```

### 3. Run the pipeline
```bash
featurization-cli run --working-dir /path/to/workspace
```

## 🧠 What it produces
Main outputs:
- `featurized_data.csv` — consolidated engineered dataset
- `model_ready_numeric_data.csv` — numeric export for modeling

The pipeline also creates diagnostic artifacts and any configured feature advisor artifacts.

## � Feature advisor: model-aware featurization guidance
The feature advisor is a value-added service that reads workspace metadata and the input dataset, then recommends how to treat categorical, numeric, hierarchical, and text attributes for your downstream model intent.

### Why use it
- recommends native categorical handling for `catboost`, `xgboost`, and `lightgbm`
- recommends low-count categorical or hierarchical encoding for long-tail categories
- recommends text featurization strategies when metadata indicates free-text fields
- writes both CSV and Markdown recommendation artifacts for review

### CLI usage
```bash
featurization-cli advise \
  --working-dir /path/to/workspace \
  --metadata-file data/dd_cleaner/sba_loans_metadata_table.csv \
  --model-intent catboost \
  --ollama-model llama2
```

Optional alternatives:
- use `--use-mock` for local validation without an LLM
- use `--llm-response-file /path/to/response.json` to replay a saved LLM output

### Python usage
```python
from featurization.notebook_utils import build_notebook_resolver
from featurization.feature_advisor_util import FeatureAdvisorUtil, FeatureAdvisorPromptConfig
import pandas as pd

resolver = build_notebook_resolver('/path/to/notebook')
prompt_config = FeatureAdvisorPromptConfig.load_from_package()
advisor = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

metadata = pd.read_csv(resolver.metadata_path)
recommendations = advisor.recommend(
    metadata=metadata,
    model_intent='catboost',
    use_rules=True,
)
print(recommendations.head())
```

### Output files
By default the advisor writes recommendations to:
- `data/<featurization_output_dir>/feature_advisor/feature_advisor_recommendations.csv`
- `data/<featurization_output_dir>/feature_advisor/feature_advisor_recommendations.md`

## �🧱 How it works
The pipeline is built from stage wrappers in `featurization_scripts/featurization.py`. Each stage:
- receives the current context and stage config
- returns a DataFrame
- is merged horizontally into the final dataset

Key principles:
- stable `record_id` anchoring for row alignment
- stage behavior driven by `featurizer_config.yaml`
- fit artifacts on train only, then use them for val/active transformation
- active reconciliation aligned to modeled feature space before merge

## 🧩 Supported workflows
- **Cross-sectional featurization**: one row per input record
- **Survival featurization**: flatten event or interval history into one row per subject

If you need survival guidance, see `documents/survival_featurization_pipeline.md`.
For regular workflows, see `documents/user_guide_cs_featurization.md`.

## 🛠️ Package components
- `src/featurization/cli.py` — CLI entry points
- `src/featurization/core/` — pipeline initialization and path coordination
- `src/tabular/` — reusable feature engineering and transformation logic
- `featurizer_config.yaml` — workspace-level configuration blueprint

## 🧪 Running tests
Run the core validation tests:

```bash
pytest -q tests/test_sba_pipeline.py tests/test_survival_prep.py tests/test_survival_featurizer_pipeline.py
```

## 📁 Where to look next
- `documents/client_onboarding.md`
- `documents/sba_pipeline_featurization.md`
- `documents/config_blueprint.md`
- `documents/path_coordinator_function.md`
- `documents/user_guide_cs_featurization.md`
- `documents/survival_featurization_pipeline.md`

## 💡 Notes for users
- `featurizer_config.yaml` anchors are workspace-relative.
- keep stage wrappers thin and reusable logic in `src/tabular/`.
- this package is designed to preserve leakage-safe feature engineering across train/validation/active splits.
