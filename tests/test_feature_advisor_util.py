import os
import pandas as pd
import pytest

from featurization.feature_advisor_util import (
    FeatureAdvisorPromptConfig,
    FeatureAdvisorUtil,
)
from featurization.core.path_coordinator import PathCoordinator


class DummyResolver(PathCoordinator):
    def __init__(self, working_dir: str):
        super().__init__(working_dir=working_dir, config={"featurization_output_dir": "featurization"})


def test_feature_advisor_prompt_config_loads_from_package():
    config = FeatureAdvisorPromptConfig.load_from_package()
    assert "system" in config.prompt_template
    assert "user" in config.prompt_template
    assert "format_instructions" in config.prompt_template


def test_feature_advisor_build_prompt_contains_metadata(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [{"attribute": "city", "logical_type": "categorical"}]
    )
    prompt = util.build_prompt(metadata=metadata, model_intent="catboost")

    assert "city" in prompt
    assert "catboost" in prompt
    assert "Metadata records" in prompt


def test_feature_advisor_build_prompt_normalizes_attribute_name_alias(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [{"attribute_name": "city", "logical_type": "categorical"}]
    )
    prompt = util.build_prompt(metadata=metadata, model_intent="catboost")

    assert "city" in prompt
    assert "attribute" in prompt
    assert "Metadata records" in prompt


def test_feature_advisor_parse_advice_and_save(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    llm_response = '[{"attribute": "city", "recommended_method": "Native CatBoost Handling", "rationale": "CatBoost processes categorical variables natively and avoids leakage when fit on train and applied to validation."}]'
    recommendations = util.parse_advice(llm_response)

    assert list(recommendations.columns) == ["attribute", "recommended_method", "rationale"]
    assert recommendations.iloc[0]["attribute"] == "city"

    util.save_recommendations(recommendations)
    assert os.path.isfile(util.recommendations_csv_path)
    assert os.path.isfile(util.recommendations_md_path)


def test_feature_advisor_ollama_response_fn_uses_subprocess(tmp_path, monkeypatch):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    class DummyCompletedProcess:
        def __init__(self, stdout, returncode=0, stderr=""):
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = stderr

    def fake_run(command, input, text, capture_output, timeout):
        assert command[:3] == ["ollama", "run", "test-model"]
        return DummyCompletedProcess('[{"attribute": "city", "recommended_method": "Native CatBoost Handling", "rationale": "Mocked live response."}]')

    monkeypatch.setattr(util, "_locate_ollama_binary", lambda: "ollama")
    monkeypatch.setattr(__import__("subprocess"), "run", fake_run)

    llm_fn = util.llm_response_fn_from_ollama_model("test-model", timeout_seconds=15)
    response = llm_fn("some prompt")

    assert "Native CatBoost Handling" in response


def test_feature_advisor_recommend_requires_llm_response_fn(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [{"attribute": "city", "logical_type": "categorical"}]
    )

    with pytest.raises(ValueError, match="llm_response_fn callable is required"):
        util.recommend(metadata=metadata)


def test_feature_advisor_recommend_from_rules_returns_dataframe(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [
            {"attribute": "naicscode", "logical_type": "categorical", "physical_type": "string"},
            {"attribute": "loan_desc", "logical_type": "text", "physical_type": "text"},
            {"attribute": "loan_amount", "logical_type": "numeric", "physical_type": "float"},
        ]
    )

    recommendations = util.recommend(metadata=metadata, model_intent="catboost", use_rules=True)

    assert len(recommendations) == 3
    assert recommendations.loc[recommendations["attribute"] == "naicscode", "recommended_method"].iloc[0] == "hierarchical_low_count_var_encoding"
    assert "SentenceTransformer" in recommendations.loc[recommendations["attribute"] == "loan_desc", "recommended_method"].iloc[0]
    assert recommendations.loc[recommendations["attribute"] == "loan_amount", "recommended_method"].iloc[0] == "No encoding required"


def test_feature_advisor_recommend_from_rules_uses_input_data_and_model_intent(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [
            {"attribute": "loan_desc"},
            {"attribute": "borrower_city"},
            {"attribute": "loan_amount"},
        ]
    )
    input_data = pd.DataFrame(
        {
            "loan_desc": ["Small business loan", "Office renovation"],
            "borrower_city": ["Springfield", "Shelbyville"],
            "loan_amount": [120000.0, 80000.0],
        }
    )

    recommendations = util.recommend(
        metadata=metadata,
        model_intent="linear_model",
        input_data=input_data,
        use_rules=True,
    )

    assert len(recommendations) == 3
    assert recommendations.loc[recommendations["attribute"] == "loan_desc", "recommended_method"].iloc[0] == "SentenceTransformer"
    assert recommendations.loc[recommendations["attribute"] == "borrower_city", "recommended_method"].iloc[0] == "low_count_cat_var_encoding + target_encoding"
    assert recommendations.loc[recommendations["attribute"] == "loan_amount", "recommended_method"].iloc[0] == "No encoding required"


def test_feature_advisor_recommend_from_rules_detects_native_gbm_intent(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [{"attribute": "borrower_city", "logical_type": "categorical", "physical_type": "string"}]
    )

    recommendations = util.recommend(metadata=metadata, model_intent="xgboost", use_rules=True)

    assert recommendations.iloc[0]["recommended_method"] == "Native Xgboost Handling"


def test_feature_advisor_recommend_from_rules_appends_longitudinal_guidance(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    resolver.config["structural_type"] = "longitudinal"
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [{"attribute": "borrower_city", "logical_type": "categorical", "physical_type": "string"}]
    )

    recommendations = util.recommend(metadata=metadata, model_intent="linear_model", use_rules=True)

    assert "longitudinal" in recommendations.iloc[0]["rationale"].lower()
    assert "structural summary wide form" in recommendations.iloc[0]["rationale"].lower()


def test_feature_advisor_recommend_from_rules_appends_wide_and_short_guidance(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    resolver.config["structural_type"] = "wide and short"
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [
            {"attribute": "borrower_city", "logical_type": "categorical", "physical_type": "string"},
            {"attribute": "loan_amount", "logical_type": "numeric", "physical_type": "float"},
        ]
    )

    recommendations = util.recommend(metadata=metadata, model_intent="linear_model", use_rules=True)

    assert len(recommendations) == 1
    assert recommendations.iloc[0]["attribute"] == "dataset"
    assert recommendations.iloc[0]["recommended_method"] == "Feature selection recommended"
    assert "wide and short" in recommendations.iloc[0]["rationale"].lower()
    assert "feature selection" in recommendations.iloc[0]["rationale"].lower()


def test_feature_advisor_recommend_short_circuits_for_wide_and_short_without_llm(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    resolver.config["structural_type"] = "wide and short"
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [
            {"attribute": "borrower_city", "logical_type": "categorical", "physical_type": "string"},
            {"attribute": "loan_amount", "logical_type": "numeric", "physical_type": "float"},
        ]
    )

    recommendations = util.recommend(metadata=metadata, model_intent="xgboost", use_rules=False)

    assert len(recommendations) == 1
    assert recommendations.iloc[0]["recommended_method"] == "Feature selection recommended"
    assert "wide and short" in recommendations.iloc[0]["rationale"].lower()


def test_feature_advisor_build_prompt_includes_longitudinal_context(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    resolver.config["structural_type"] = "longitudinal"
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [{"attribute": "city", "logical_type": "categorical"}]
    )
    prompt = util.build_prompt(metadata=metadata, model_intent="catboost")

    assert "dataset structural type: longitudinal" in prompt.lower()
    assert "structural summary wide form" in prompt.lower()


def test_feature_advisor_build_prompt_includes_wide_and_short_context(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    resolver.config["structural_type"] = "wide and short"
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    metadata = pd.DataFrame(
        [{"attribute": "city", "logical_type": "categorical"}]
    )
    prompt = util.build_prompt(metadata=metadata, model_intent="catboost")

    assert "dataset structural type: wide and short" in prompt.lower()
    assert "feature selection methods" in prompt.lower()
    assert "do not perform attribute-level featurization recommendations" in prompt.lower()


def test_feature_advisor_parse_advice_accepts_dict_response(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    llm_response = '{"city": {"attribute": "city", "recommended_method": "Native Model Handling", "rationale": "Safe."}}'
    recommendations = util.parse_advice(llm_response)

    assert len(recommendations) == 1
    assert recommendations.iloc[0]["attribute"] == "city"


def test_feature_advisor_parse_advice_sanitizes_ansi(tmp_path):
    resolver = DummyResolver(str(tmp_path))
    prompt_config = FeatureAdvisorPromptConfig.load_from_package()
    util = FeatureAdvisorUtil(resolver=resolver, prompt_config=prompt_config)

    llm_response = '{"city": {"attribute": "city", "recommended_method": "Native\x1b[31m Handling", "rationale": "Safe."}}'
    recommendations = util.parse_advice(llm_response)

    assert recommendations.iloc[0]["recommended_method"] == "Native Handling"
