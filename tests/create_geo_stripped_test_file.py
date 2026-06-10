import os
import yaml
import pandas as pd

def generate_stripped_dataset():
    # Base configuration targets
    config_path = "/home/rajiv/programming/featurization/featurizer_config.yaml"
    working_dir = "/home/rajiv/programming/kmds_descriptive_analytics/kmds_sba_loans"
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration not found at: {config_path}")
        return
        
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    # Gather structural workspace attributes
    dd_dir = config.get("dd_parsing_output_dir", "dd_analysis_results")
    dd_file = config.get("dd_parsing_summary_file", "sba_analysis_results.csv")
    clean_dir = config.get("dd_cleaner_output_dir", "dd_cleaner_results")
    clean_file = config.get("cleaned_file_from_dd_cleaner", "feature_selection_ready.csv")
    
    # Path Resolution Spec
    dd_path = os.path.join(working_dir, "data_dictionary", dd_dir, dd_file)
    source_file = os.path.join(working_dir, "data", clean_dir, clean_file)
    output_file = os.path.join(working_dir, "data", clean_dir, "general_non_geo_dataset.csv")

    if not os.path.exists(dd_path):
        print(f"❌ Data dictionary summary file not found at: {dd_path}")
        return
        
    print(f"🔍 Parsing data dictionary configurations from: {dd_path}")
    
    # Read the file first as plain text to see if the first line is the LLM signature comment
    with open(dd_path, "r") as f:
        first_line = f.readline()
        
    if "DD-PARSER-SIGNATURE" in first_line:
        print("   🤖 LLM Signature block identified. Skipping first line metadata tracking...")
        df_dd = pd.read_csv(dd_path, skiprows=1)
    else:
        df_dd = pd.read_csv(dd_path)

    # Find the meta columns flexibly
    geo_flag_col = next((c for c in df_dd.columns if "geo" in c.lower()), None)
    attr_col = next((c for c in df_dd.columns if "attr" in c.lower() or "col" in c.lower() or "name" in c.lower()), None)
    
    if not geo_flag_col or not attr_col:
        print(f"❌ Error matching meta-columns in Data Dictionary. Discovered headers: {list(df_dd.columns)}")
        return

    # Extract strings/bool maps for any items tagged geographic
    geo_rows = df_dd[df_dd[geo_flag_col].astype(str).str.lower().str.strip().isin(['true', '1', 'yes', 'y'])]
    
    # Build a lowercase lookup list of columns we WANT to drop
    geo_columns_to_drop = geo_rows[attr_col].astype(str).str.strip().str.lower().tolist()

    print(f"🎯 Dynamic Extraction: Found {len(geo_columns_to_drop)} geo-attributes to drop from dictionary data rules.")

    if not os.path.exists(source_file):
        print(f"❌ Target data file not found at: {source_file}")
        return

    print(f"📥 Loading original analytical data matrix from: {source_file}")
    df_data = pd.read_csv(source_file, low_memory=False)

    # Match case-insensitively, but keep the exact name from df_data
    metadata_drops = [
        col for col in df_data.columns 
        if str(col).lower().strip() in geo_columns_to_drop
    ]
    
    # Wildcard catch for previously engineered runtime geo search string columns
    engineered_geo_drops = [
        col for col in df_data.columns 
        if "geo" in str(col).lower() and col not in metadata_drops
    ]
    
    all_drops = metadata_drops + engineered_geo_drops
    
    # Drop using the exact column names discovered in the dataframe
    df_stripped = df_data.drop(columns=all_drops, errors='ignore')

    print(f"✂️ Dropped {len(metadata_drops)} metadata geo columns and {len(engineered_geo_drops)} engineered geo extensions.")
    
    # --- TERMINAL PRINTER UPGRADE ---
    print("\n📋 Remaining Columns in Stripped Dataset:")
    print("-" * 50)
    for idx, col in enumerate(df_stripped.columns, start=1):
        print(f"  {idx:02d}. {col}")
    print("-" * 50)
    print(f"📦 Total Remaining Columns: {len(df_stripped.columns)}\n")
    # ---------------------------------

    # Export out general structured framework simulator preserving exact data-level casing
    df_stripped.to_csv(output_file, index=False)
    print(f"🏁 General non-geo baseline simulation file exported to: {output_file}")

if __name__ == "__main__":
    generate_stripped_dataset()
