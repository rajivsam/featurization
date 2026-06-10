import os
import yaml
import pandas as pd
from featurization.core.sequential_pipeline_runner import PipelineRunner
from featurization.core.path_coordinator import PathCoordinator


def _col_as_series(df: pd.DataFrame, col_name: str) -> pd.Series:
    """Returns a single Series even if duplicate-named columns are present."""
    selected = df[col_name]
    if isinstance(selected, pd.DataFrame):
        return selected.iloc[:, 0]
    return selected

def test_borrower_geo_pipeline_execution():
    """
    Verifies end-to-end execution of the canonical SBA featurization pipeline.
    Ensures one consolidated output artifact is persisted with expected attributes.
    """
    working_dir = "/home/rajiv/programming/dd_parser_cleaner_migration/sba_migration"
    config_path = os.path.join(working_dir, "featurizer_config.yaml")
    
    print(f"🧪 Running Borrower Geo Pipeline Test: {working_dir}")
    
    if not os.path.exists(config_path):
        print(f"❌ Error: Authoritative config missing at {config_path}.")
        return

    # 1. Load baseline config and override pipeline with single stage
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    configured_methods = [stage.get("method") for stage in (config.get("pipeline") or [])]
    expected_methods = [
        "record_id_definition",
        "borrower_geo_coding",
        "low_count_featurization_of_cat_vars",
        "hierarchical_low_count_var_encoding",
        "loan_status_recoding",
        "filter_modeling_universe",
        "stratified_train_val_split",
        "target_encode_categorical_vars",
        "harmonize_and_project_feature_space",
        "merge_modeled_and_active_partitions",
    ]
    missing_methods = [m for m in expected_methods if m not in configured_methods]
    assert not missing_methods, f"Pipeline config is missing expected methods: {missing_methods}"
    
    # 2. Execute Runner
    runner = PipelineRunner(working_dir=working_dir, config=config)
    final_df = runner.accumulate_stages()
    
    # 3. Assertions
    assert final_df.index.name == "record_id", "Index was not promoted to 'record_id' as expected."
    assert "borrower_latitude" in final_df.columns, "Column 'borrower_latitude' missing from output."
    assert "borrower_longitude" in final_df.columns, "Column 'borrower_longitude' missing from output."
    assert any("_rcs" in col for col in final_df.columns), "No recoded-for-support columns found from categorical stage."
    assert "naicscode_rcs" in final_df.columns, "Column 'naicscode_rcs' missing from hierarchical NAICS stage."

    # Assertions for the new 'loan_status_r' column
    assert "loan_status_r" in final_df.columns, "Column 'loan_status_r' missing from output."
    # Check if the recoded values are within the expected set {-1, 0, 1}
    loan_status_series = _col_as_series(final_df, "loan_status_r")
    unique_recoded_values = loan_status_series.dropna().unique()
    expected_recoded_values = {-1.0, 0.0, 1.0}
    assert all(val in expected_recoded_values for val in unique_recoded_values), \
        f"Unexpected values found in 'loan_status_r': {unique_recoded_values}"
    assert loan_status_series.count() > 0, "No non-NaN values found in 'loan_status_r'."
    assert "dataset_split" in final_df.columns, "Column 'dataset_split' missing from split stage."
    split_series = _col_as_series(final_df, "dataset_split")
    split_values = set(split_series.dropna().unique().tolist())
    assert split_values.issubset({"train", "val", "active"}), f"Unexpected split values found: {split_values}"
    assert any(col.endswith("_te") for col in final_df.columns), "No target-encoded columns found from target encoding stage."
    assert "dataset_partition" in final_df.columns, "Column 'dataset_partition' missing from merge stage."
    partition_series = _col_as_series(final_df, "dataset_partition")
    partition_values = set(partition_series.dropna().unique().tolist())
    assert partition_values.issubset({"modeled", "active"}), f"Unexpected partition values found: {partition_values}"

    # After filter stage, active class (-1) should be removed from modeling universe.
    modeled_target_values = set(
        loan_status_series.loc[partition_series == "modeled"].dropna().unique().tolist()
    )
    assert modeled_target_values.issubset({0.0, 1.0}), f"Filtered modeling universe has unexpected labels: {modeled_target_values}"

    # Assert persisted single output artifact exists and includes the same key attributes.
    resolver = PathCoordinator(working_dir=working_dir, config=config)
    assert os.path.exists(resolver.featurized_dataset_path), (
        f"Expected featurized output file missing at {resolver.featurized_dataset_path}"
    )
    persisted_df = pd.read_csv(resolver.featurized_dataset_path)
    required_columns = [
        "borrower_latitude",
        "borrower_longitude",
        "naicscode_rcs",
        "loan_status_r",
        "dataset_split",
        "dataset_partition",
    ]
    missing_columns = [c for c in required_columns if c not in persisted_df.columns]
    assert not missing_columns, f"Persisted output missing expected columns: {missing_columns}"

    # Assert model-ready numeric export exists and is numeric-only.
    assert os.path.exists(resolver.model_ready_dataset_path), (
        f"Expected model-ready output missing at {resolver.model_ready_dataset_path}"
    )
    model_ready_df = pd.read_csv(resolver.model_ready_dataset_path)
    non_numeric_cols = model_ready_df.select_dtypes(exclude=["number", "bool"]).columns.tolist()
    assert not non_numeric_cols, f"Model-ready export contains non-numeric columns: {non_numeric_cols}"
    
    print(f"✅ Single-stage pipeline success. Discovered columns: {[c for c in final_df.columns if 'borrower' in c or 'loan_status_r' in c]}")

if __name__ == "__main__":
    test_borrower_geo_pipeline_execution()