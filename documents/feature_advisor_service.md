# Feature Advisor Service

The package contains a feature advisor service that generates actionable featurization recommendations from:

- the metadata table (`resolver.metadata_path`)
- the input dataset (`resolver.featurization_input_path`)
- explicit downstream model intent (`model_intent`)

## Value Proposition

This is a value-added service for teams who want a diagnostic recommendation layer before they wire a pipeline.

- Offers metadata-driven guidance rather than generic type rules
- Prefers native categorical handling for `catboost`, `xgboost`, and `lightgbm`
- Falls back to explicit encoder recommendations for non-GBDT modeling targets
- Produces CSV and Markdown recommendation artifacts for review

## How to use

From the CLI:

featurization-cli advise --working-dir /path/to/workspace --model-intent catboost

From Python:

```python
from featurization.notebook_utils import build_notebook_resolver
from featurization.feature_advisor_util import FeatureAdvisorUtil, FeatureAdvisorPromptConfig

resolver = build_notebook_resolver('/path/to/notebook')
prompt_config = FeatureAdvisorPromptConfig.load_from_package()
advisor = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

metadata = pd.read_csv(resolver.metadata_path)
recommendations = advisor.recommend(
    metadata=metadata,
    model_intent='catboost',
    use_rules=True,
)
```

## Demo

Contact the maintainer if you want to see a hands-on demo of the feature advisor workflow.