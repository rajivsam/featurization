import os
import yaml
import pandas as pd
from featurization.core.sequential_pipeline_runner import PipelineRunner

def test_borrower_geo_pipeline_execution():
    """
    Verifies the execution of a single-stage pipeline implementing 
    borrower geo featurization.
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
    
    config['pipeline'] = [
        {
            "name": "Record ID Generation",
            "method": "record_id_definition",
            "entity": "System",
            "sub_filter": "System"
        },
        {
            "name": "Borrower Geo Coding",
            "method": "borrower_geo_coding",
            "entity": "geographic",
            "sub_filter": "Borrower"
        },
        {
            "name": "Low Count Categorical Encoding",
            "method": "low_count_featurization_of_cat_vars",
            "entity": "categorical",
            "sub_filter": "low_count",
            "drop_filter": ["loanstatus", "naicscode"]
        },
        # NEW STAGE: Loan Status Recoding
        {
            "name": "Loan Status Recoding",
            "method": "loan_status_recoding",
            "entity": "System", # This stage operates on a core system column
            "sub_filter": "Loan" # Categorizing it under 'Loan' entity
        }
    ]
    
    # 2. Execute Runner
    runner = PipelineRunner(working_dir=working_dir, config=config)
    final_df = runner.accumulate_stages()
    
    # 3. Assertions
    assert final_df.index.name == "record_id", "Index was not promoted to 'record_id' as expected."
    assert "borrower_latitude" in final_df.columns, "Column 'borrower_latitude' missing from output."
    assert "borrower_longitude" in final_df.columns, "Column 'borrower_longitude' missing from output."
    assert any("_rcs" in col for col in final_df.columns), "No recoded-for-support columns found from categorical stage."

    # Assertions for the new 'loan_status_r' column
    assert "loan_status_r" in final_df.columns, "Column 'loan_status_r' missing from output."
    # Check if the recoded values are within the expected set {-1, 0, 1}
    unique_recoded_values = final_df['loan_status_r'].dropna().unique()
    expected_recoded_values = {-1.0, 0.0, 1.0}
    assert all(val in expected_recoded_values for val in unique_recoded_values), \
        f"Unexpected values found in 'loan_status_r': {unique_recoded_values}"
    assert final_df['loan_status_r'].count() > 0, "No non-NaN values found in 'loan_status_r'."
    
    print(f"✅ Single-stage pipeline success. Discovered columns: {[c for c in final_df.columns if 'borrower' in c or 'loan_status_r' in c]}")

if __name__ == "__main__":
    test_borrower_geo_pipeline_execution()