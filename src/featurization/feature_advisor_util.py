from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

import pandas as pd
import yaml
from importlib import resources

from featurization.core.path_coordinator import PathCoordinator
from featurization.notebook_utils import build_notebook_resolver

DEFAULT_PROMPT_CONFIG_NAME = "feature_advisor_prompt.yaml"
DEFAULT_FEATURE_ADVISOR_DIR = "feature_advisor"


@dataclass
class FeatureAdvisorPromptConfig:
    prompt_template: Dict[str, str]

    @classmethod
    def load_from_package(cls, config_name: str = DEFAULT_PROMPT_CONFIG_NAME) -> "FeatureAdvisorPromptConfig":
        prompt_dir = resources.files("featurization").joinpath("prompts")
        config_path = prompt_dir.joinpath(config_name)
        if not config_path.exists():
            raise FileNotFoundError(
                f"Feature advisor prompt config not found in package resources: {config_name}"
            )

        with config_path.open("r", encoding="utf-8") as fh:
            content = yaml.safe_load(fh) or {}

        if "prompt" not in content:
            raise ValueError("Invalid feature advisor prompt config: missing 'prompt' section.")

        return cls(prompt_template=content["prompt"])


class FeatureAdvisorUtil:
    def __init__(self, resolver: PathCoordinator, prompt_config: FeatureAdvisorPromptConfig):
        self.resolver = resolver
        self.prompt_config = prompt_config

    @classmethod
    def from_notebook_dir(cls, notebook_dir: str, prompt_config_name: str = DEFAULT_PROMPT_CONFIG_NAME) -> "FeatureAdvisorUtil":
        resolver = build_notebook_resolver(notebook_dir)
        prompt_config = FeatureAdvisorPromptConfig.load_from_package(prompt_config_name)
        return cls(resolver=resolver, prompt_config=prompt_config)

    @property
    def feature_advisor_dir(self) -> str:
        output_dir = self.resolver.config.get("featurization_output_dir", "featurization")
        return os.path.join(
            self.resolver.working_dir,
            "data",
            output_dir,
            DEFAULT_FEATURE_ADVISOR_DIR,
        )

    @property
    def recommendations_csv_path(self) -> str:
        return os.path.join(self.feature_advisor_dir, "feature_advisor_recommendations.csv")

    @property
    def recommendations_md_path(self) -> str:
        return os.path.join(self.feature_advisor_dir, "feature_advisor_recommendations.md")

    def get_output_paths(self) -> Dict[str, str]:
        return {
            "feature_advisor_dir": self.feature_advisor_dir,
            "recommendations_csv_path": self.recommendations_csv_path,
            "recommendations_md_path": self.recommendations_md_path,
        }

    def _normalize_metadata_columns(self, metadata: pd.DataFrame) -> pd.DataFrame:
        if "attribute" in metadata.columns:
            return metadata.copy()

        alias_columns = {
            "attribute_name": "attribute",
            "Field Name": "attribute",
            "field_name": "attribute",
            "field": "attribute",
        }
        existing_aliases = [src for src in alias_columns if src in metadata.columns]

        if not existing_aliases:
            raise ValueError(
                "Metadata must contain an 'attribute' column or one of the alias columns: "
                f"{', '.join(alias_columns.keys())}. Found: {', '.join(metadata.columns)}"
            )

        normalized = metadata.copy()
        for src in existing_aliases:
            normalized = normalized.rename(columns={src: alias_columns[src]})
            break
        return normalized

    def _load_input_data(self) -> pd.DataFrame:
        input_path = self.resolver.featurization_input_path
        if os.path.isfile(input_path):
            return pd.read_csv(input_path)
        return pd.DataFrame()

    def _infer_types_from_data(self, attribute: str, input_data: pd.DataFrame) -> tuple[str, str]:
        if input_data is None or input_data.empty or attribute not in input_data.columns:
            return "", ""

        dtype = input_data[attribute].dtype
        if pd.api.types.is_numeric_dtype(dtype):
            return "numeric", str(dtype)
        if pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype):
            if self._is_text_field(attribute, "", ""):
                return "text", "string"
            return "categorical", "string"
        return "", str(dtype)

    @staticmethod
    def _normalize_string(value: object) -> str:
        if value is None:
            return ""
        return str(value).lower().strip()

    def _is_hierarchical_field(self, attribute: str) -> bool:
        attribute = attribute.lower()
        return "naics" in attribute

    def _is_text_field(self, attribute: str, logical_type: str, physical_type: str) -> bool:
        text_indicators = [
            "text",
            "desc",
            "description",
            "comment",
            "note",
            "review",
            "summary",
            "reason",
            "story",
            "message",
            "title",
            "subject",
        ]
        attribute_lower = attribute.lower()
        if logical_type in {"text", "string", "varchar", "char", "clob", "ntext"}:
            return True
        if any(keyword in attribute_lower for keyword in text_indicators):
            return True
        if "text" in physical_type:
            return True
        return False

    def _is_numeric_field(self, logical_type: str, physical_type: str) -> bool:
        return logical_type in {"numeric", "number", "integer", "int", "float", "double", "decimal"} or \
            any(keyword in physical_type for keyword in ["int", "float", "double", "decimal", "numeric"])

    def _recommend_method_for_record(self, record: dict, model_intent: str, input_data: pd.DataFrame | None = None) -> tuple[str, str]:
        attribute = str(record.get("attribute", "")).strip()
        logical_type = self._normalize_string(record.get("logical_type"))
        physical_type = self._normalize_string(record.get("physical_type") or record.get("data_type"))
        attribute_lower = attribute.lower()
        model_intent_normalized = self._normalize_string(model_intent)
        native_gbm_intents = {"catboost", "xgboost", "lightgbm"}

        if (not logical_type or not physical_type) and input_data is not None:
            inferred_logical, inferred_physical = self._infer_types_from_data(attribute, input_data)
            logical_type = logical_type or inferred_logical
            physical_type = physical_type or inferred_physical

        if self._is_text_field(attribute_lower, logical_type, physical_type):
            if any(keyword in attribute_lower for keyword in ["desc", "description", "comment", "review", "reason", "story"]):
                return (
                    "SentenceTransformer",
                    "Long-form or descriptive text field. Use a stateless SentenceTransformer embedder to capture semantic context and avoid leaking validation data through train-only vocabulary fitting.",
                )
            return (
                "TF-IDF + TruncatedSVD",
                "Short text or keyword-style field. Fit sparse TF-IDF on train only and compress with TruncatedSVD to preserve train/validation safety while limiting sparse dimensionality.",
            )

        if self._is_hierarchical_field(attribute_lower):
            return (
                "hierarchical_low_count_var_encoding",
                "Hierarchical or geographic long-tail categorical code. Use right-side masking to preserve parent-level industry/geo structure while meeting minimum support on train data.",
            )

        if self._is_numeric_field(logical_type, physical_type):
            return (
                "No encoding required",
                "Numeric feature should be passed through the numeric pipeline without additional categorical encoding, preserving train/validation artifact separation.",
            )

        if logical_type in {"categorical", "category", "enum"} or physical_type in {"string", "varchar", "char", "object"}:
            if model_intent_normalized in native_gbm_intents:
                return (
                    f"Native {model_intent_normalized.title()} Handling",
                    f"Use native {model_intent_normalized.title()} categorical handling for this field. This avoids manual encoding overhead and preserves train/validation safety through the model's built-in leakage-aware categorical algorithm.",
                )
            return (
                "low_count_cat_var_encoding + target_encoding",
                "Use low-count categorical grouping on train data followed by target encoding to produce numeric model-ready features while avoiding unseen categories during validation/active scoring.",
            )

        return (
            "Review metadata",
            "The field does not match a recognized categorical, numeric, or text featurization pattern. Validate whether it should be treated as a specialized text or hierarchical categorical field.",
        )

    def recommend_from_rules(
        self,
        metadata: pd.DataFrame,
        model_intent: str = "gbm",
        input_data: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        normalized_metadata = self._normalize_metadata_columns(metadata)
        records = normalized_metadata.to_dict(orient="records")
        recommendations = []
        for record in records:
            attribute = str(record.get("attribute", "")).strip()
            if not attribute:
                continue
            recommended_method, rationale = self._recommend_method_for_record(
                record,
                model_intent,
                input_data=input_data,
            )
            recommendations.append(
                {
                    "attribute": attribute,
                    "recommended_method": recommended_method,
                    "rationale": rationale,
                }
            )
        return pd.DataFrame(recommendations)

    def build_prompt(self, metadata: pd.DataFrame, model_intent: str = "gbm") -> str:
        normalized_metadata = self._normalize_metadata_columns(metadata)

        system_prompt = self.prompt_config.prompt_template.get("system", "")
        user_prompt = self.prompt_config.prompt_template.get("user", "")
        format_instructions = self.prompt_config.prompt_template.get("format_instructions", "")

        metadata_json = normalized_metadata.to_dict(orient="records")
        metadata_serialized = json.dumps(metadata_json, indent=2, default=str)

        prompt = (
            f"{system_prompt}\n\n"
            f"{user_prompt}\n\n"
            f"Model intent: {model_intent}\n\n"
            f"Metadata records:\n{metadata_serialized}\n\n"
            f"{format_instructions}"
        )
        return prompt

    def _sanitize_llm_response(self, llm_response: str) -> str:
        # Remove ANSI/terminal control sequences and invalid JSON control characters.
        cleaned = re.sub(r"\x1B[@-_][0-?]*[ -/]*[@-~]", "", llm_response)
        cleaned = re.sub(r"[\x00-\x1F]+", " ", cleaned)
        return cleaned.strip()

    def _normalize_llm_response(self, cleaned_response: str) -> str:
        # Try to extract a JSON substring if there is surrounding text.
        first_brace = cleaned_response.find("{")
        first_bracket = cleaned_response.find("[")
        if first_brace == -1 and first_bracket == -1:
            return cleaned_response

        start = min(x for x in (first_brace, first_bracket) if x != -1)
        end_brace = cleaned_response.rfind("}")
        end_bracket = cleaned_response.rfind("]")
        if end_brace == -1 and end_bracket == -1:
            return cleaned_response

        end = max(end_brace, end_bracket)
        return cleaned_response[start:end + 1]

    def parse_advice(self, llm_response: str) -> pd.DataFrame:
        cleaned_response = self._sanitize_llm_response(llm_response)
        normalized_response = self._normalize_llm_response(cleaned_response)

        try:
            parsed = json.loads(normalized_response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Unable to parse advisor response as JSON. "
                "Ensure the response is a JSON array or dict of objects. "
                f"Sanitized response preview: {normalized_response[:400]!r}"
            ) from exc

        if isinstance(parsed, dict):
            parsed = list(parsed.values())

        if not isinstance(parsed, list):
            raise ValueError("Advisor response must be a JSON array of recommendation objects.")

        result = pd.DataFrame(parsed)
        expected_columns = {"attribute", "recommended_method", "rationale"}
        if not expected_columns.issubset(set(result.columns)):
            raise ValueError(
                "Advisor JSON response must include the keys: attribute, recommended_method, rationale."
            )
        return result

    def save_recommendations(self, recommendations: pd.DataFrame) -> None:
        os.makedirs(self.feature_advisor_dir, exist_ok=True)
        recommendations.to_csv(self.recommendations_csv_path, index=False)

        markdown_lines = ["# Feature Advisor Recommendations", ""]
        for _, row in recommendations.iterrows():
            markdown_lines.append(f"## {row['attribute']}")
            markdown_lines.append(f"- Recommended method: {row['recommended_method']}")
            markdown_lines.append(f"- Rationale: {row['rationale']}")
            markdown_lines.append("")

        with open(self.recommendations_md_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(markdown_lines))

    def _locate_ollama_binary(self) -> str:
        ollama_path = shutil.which("ollama")
        if not ollama_path:
            raise FileNotFoundError(
                "Ollama CLI not found in PATH. Install Ollama or update your PATH to include it."
            )
        return ollama_path

    def _call_ollama_model(self, prompt: str, model_name: str, timeout_seconds: int = 300) -> str:
        ollama_binary = self._locate_ollama_binary()
        command = [
            ollama_binary,
            "run",
            model_name,
            "--format",
            "json",
            "--hidethinking",
        ]
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Ollama model invocation failed: "
                + (completed.stderr.strip() or completed.stdout.strip())
            )
        return completed.stdout.strip()

    def llm_response_fn_from_ollama_model(
        self,
        model_name: str,
        timeout_seconds: int = 300,
    ) -> Callable[[str], str]:
        def llm_response_fn(prompt: str) -> str:
            return self._call_ollama_model(
                prompt=prompt,
                model_name=model_name,
                timeout_seconds=timeout_seconds,
            )

        return llm_response_fn

    def recommend(
        self,
        metadata: pd.DataFrame,
        model_intent: str = "gbm",
        input_data: pd.DataFrame | None = None,
        llm_response_fn: Optional[Callable[[str], str]] = None,
        use_rules: bool = False,
    ) -> pd.DataFrame:
        if use_rules:
            if input_data is None:
                input_data = self._load_input_data()
            recommendations = self.recommend_from_rules(
                metadata=metadata,
                model_intent=model_intent,
                input_data=input_data,
            )
        else:
            prompt = self.build_prompt(metadata=metadata, model_intent=model_intent)
            if llm_response_fn is None:
                raise ValueError(
                    "An llm_response_fn callable is required to execute the advisor recommendation flow."
                )

            llm_response = llm_response_fn(prompt)
            recommendations = self.parse_advice(llm_response)

        self.save_recommendations(recommendations)
        return recommendations
