import os
import yaml
import pandas as pd
from typing import Optional, Dict, List
from featurization.transforms.filters import exclusion_filter

class FeaturizationService:
    def __init__(self, working_dir: str, config_path: str = "config.yaml"):
        self.working_dir = working_dir
        
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self._resolve_paths()
        self.data: Optional[pd.DataFrame] = None

    def _resolve_paths(self):
        """Resolves project paths dynamically using configuration variables."""
        # Data dictionary paths
        dd_dir = self.config.get("dd_parsing_output_dir", "dd_analysis_results")
        dd_file = self.config.get("dd_parsing_summary_file", "sba_analysis_results.csv")
        
        # Cleaned data input paths
        clean_dir = self.config.get("dd_cleaner_output_dir", "dd_cleaner_results")
        clean_file = self.config.get("cleaned_file_from_dd_cleaner", "feature_selection_ready.csv")
        
        # Featurization output paths
        feat_dir = self.config.get("featurization_output_dir", "featurization")
        feat_file = self.config.get("featurization_output_file", "featurized_data.csv")
        
        # New configurable documentation directory paths
        doc_dir = self.config.get("feat_doc_directory", "featurization_docs")
        doc_file = self.config.get("entity_assignment_output", "entity_assignments.md")
        
        # Resolved full system targets
        self.dd_summary_path = os.path.join(self.working_dir, "data_dictionary", dd_dir, dd_file)
        self.cleaned_data_path = os.path.join(self.working_dir, "data", clean_dir, clean_file)
        self.output_data_dir = os.path.join(self.working_dir, "data", feat_dir)
        self.output_data_path = os.path.join(self.output_data_dir, feat_file)
        
        # KMDS specific documentation destination resolution
        self.report_dir = os.path.join(self.working_dir, "documents", doc_dir)
        self.report_file_path = os.path.join(self.report_dir, doc_file)

    def load_data(self):
        """Reads the source data file into memory cleanly."""
        if not os.path.exists(self.cleaned_data_path):
            raise FileNotFoundError(f"Source data not found at: {self.cleaned_data_path}")
        self.data = pd.read_csv(self.cleaned_data_path, low_memory=False)

    def extract_geo_entities(self) -> Dict[str, List[str]]:
        """Parses the data dictionary summary file to discover geographical entity maps."""
        if not os.path.exists(self.dd_summary_path):
            print(f"⚠️ Warning: Data dictionary summary file missing at {self.dd_summary_path}. Skipping geo tasks.")
            return {}

        dd_df = pd.read_csv(self.dd_summary_path, comment="#")
        dd_df.columns = [str(c).lower().strip() for c in dd_df.columns]
        
        if "is_geographical" not in dd_df.columns:
            available_cols = list(dd_df.columns)
            raise KeyError(
                f"Missing column 'is_geographical' in data dictionary file header. Found columns: {available_cols}"
            )

        geo_mask = dd_df["is_geographical"].astype(str).str.lower().str.strip() == "true"
        geo_fields = dd_df[geo_mask].copy()
        
        if geo_fields.empty:
            print("ℹ️ No geographical attributes discovered in data dictionary summary.")
            return {}
            
        col_header = "attribute_name" if "attribute_name" in dd_df.columns else "column_name"
        entity_header = "related_entity" if "related_entity" in dd_df.columns else "entity"
        
        geo_fields[entity_header] = geo_fields[entity_header].fillna("Unassigned_Entity").astype(str).str.strip()
        geo_fields[entity_header] = geo_fields[entity_header].replace("", "Unassigned_Entity")
        
        entity_map = geo_fields.groupby(entity_header)[col_header].apply(list).to_dict()
        return entity_map

    def _write_markdown_report(self, geo_entity_map: Dict[str, List[str]]):
        """Generates a structured KMDS documentation artifact for the assignments."""
        os.makedirs(self.report_dir, exist_ok=True)
        
        md_content = [
            "# KMDS Featurization Report",
            "## 🌍 Geographical Entity Assignment Summary\n",
            "The following attributes have been grouped by their related organizational entities based on data dictionary specifications. This map establishes targets for upcoming proxy coordinates and features selection processes.\n",
            "| Related Entity | Discovered Geographical Attributes |",
            "| :--- | :--- |"
        ]
        
        for entity, attributes in sorted(geo_entity_map.items()):
            attr_string = ", ".join([f"`{a}`" for a in attributes])
            md_content.append(f"| **{entity}** | {attr_string} |")
            
        with open(self.report_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        print(f"📝 Markdown tracking document generated successfully at: {self.report_file_path}")

    def orchestrate_pipeline(self, target_column: str):
        """Sequential execution manager for the featurization lifecycle."""
        print("🚀 Starting Featurization Pipeline...")
        self.load_data()

        # Step 1: Attribute Exclusion Filtering
        exclude_list = self.config.get("exclude_attributes", [])
        exclude_regex = self.config.get("exclude_regex", None)
        
        if exclude_list or exclude_regex:
            print(f"   Running exclusion filter (List: {exclude_list}, Regex: {exclude_regex})...")
            self.data = exclusion_filter(self.data, explicit_list=exclude_list, regex_pattern=exclude_regex)

        # Step 2: Parse Data Dictionary for Geo-Gating Maps
        print("🔍 Mapping geographical columns via data dictionary configuration...")
        geo_entity_map = self.extract_geo_entities()
        for entity, cols in geo_entity_map.items():
            print(f"   📍 Found Entity [{entity}] mapped to attributes: {cols}")

        # Step 3: Write Entity Assignment Report Artifact
        if geo_entity_map:
            self._write_markdown_report(geo_entity_map)

        # Step 4: Save the current state to the configured location
        print(f"💾 Creating output workspace at: {self.output_data_dir}")
        os.makedirs(self.output_data_dir, exist_ok=True)
        
        print(f"📥 Exporting filtered dataset to: {self.output_data_path}")
        self.data.to_csv(self.output_data_path, index=False)

        # [Future Steps Placeholder] Proxy coordinate engine and RF selection
        print("✅ Pipeline run complete.")
