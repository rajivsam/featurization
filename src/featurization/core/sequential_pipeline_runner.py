import os
import yaml
import pandas as pd
import importlib.util
from typing import Optional, Dict, List
from dataclasses import dataclass
from featurization.core.path_coordinator import PathCoordinator
from featurization.core.data_loader import KMDSDataLoader

@dataclass
class StageDefinition:
    """Data object for defining a pipeline stage's metadata."""
    name: str
    method: str
    entity: str
    sub_filter: str

class PipelineRunner:
    """
    Minimalist pipeline runner focused on initializing KMDS anchors and 
    accumulating horizontally concatenated datasets from defined stages.
    """
    def __init__(self, working_dir: str, config: Optional[Dict] = None):
        self.working_dir = os.path.abspath(working_dir)
        self.config_name = "featurizer_config.yaml"
        self.context = {"config": config} if config else {}
        self.stage_definitions: List[StageDefinition] = []

    def add_stage_definitions(self, definitions: List[StageDefinition]):
        """
        Registers stages into the 'pipeline' section of the featurizer_config.yaml.
        Each entry maps a stage to a specific method name in featurization.py.
        """
        # Use a temporary coordinator to find the config if not already provided
        config_path = os.path.join(self.working_dir, self.config_name)
        
        # Validation: Ensure the logic script exists before registering stages
        # (This is where PathCoordinator properties start to matter during add-stage)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration not found. Run init first: {config_path}")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}

        if "pipeline" not in config or config["pipeline"] is None:
            config["pipeline"] = []

        for dfn in definitions:
            stage_entry = {
                "name": dfn.name,
                "method": dfn.method,
                "entity": dfn.entity,
                "sub_filter": dfn.sub_filter
            }
            # Prevent duplicate registration
            if not any(s.get("name") == dfn.name for s in config["pipeline"]):
                config["pipeline"].append(stage_entry)
            if not any(d.name == dfn.name for d in self.stage_definitions):
                self.stage_definitions.append(dfn)

        with open(config_path, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    def accumulate_stages(self) -> pd.DataFrame:
        """
        Executes the pipeline by calling methods from featurization_scripts/featurization.py.
        Collects the results and concatenates them horizontally.
        """
        # Prioritize configuration provided during initialization to support test overrides
        config = self.context.get("config")
        if not config:
            config_path = os.path.join(self.working_dir, self.config_name)
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

        resolver = PathCoordinator(self.working_dir, config)
        loader = KMDSDataLoader(resolver)

        # (1) Data Load - Centralized execution context
        self.context = {
            "loader": loader,
            "resolver": resolver,
            "config": config,
            "data": loader.data,
            "metadata": loader.metadata
        }

        # (2) Resolve logic source via PathCoordinator
        scripts_file = resolver.script_logic_path
        if not os.path.exists(scripts_file):
            raise FileNotFoundError(f"Required featurization.py logic file not found at: {scripts_file}")

        spec = importlib.util.spec_from_file_location("featurization_logic", scripts_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        accumulated_dfs = []
        last_stage_df: Optional[pd.DataFrame] = None

        # (3) Iterate pipeline section and call defined methods
        pipeline_cfg = config.get("pipeline") or []
        print(f"🚀 Accumulating {len(pipeline_cfg)} featurization stages...")

        for stage_cfg in pipeline_cfg:
            method_name = stage_cfg.get("method")
            if hasattr(module, method_name):
                method = getattr(module, method_name)
                input_count = len(self.context['data'])
                print(f"   [Executing: {stage_cfg['name']} -> {method_name}] (Input records: {input_count})")
                
                # (4) Accumulate and concatenate
                df_result = method(self.context, stage_cfg)
                if isinstance(df_result, pd.DataFrame):
                    # Automatic Index Management:
                    # If a stage produces a 'record_id', we promote it to the index 
                    # for both the result and the master data context.
                    if 'record_id' in df_result.columns:
                        df_result = df_result.set_index('record_id')
                        # Align the master dataset and previous patches once record_id is derived
                        for i in range(len(accumulated_dfs)):
                            accumulated_dfs[i].index = df_result.index
                            accumulated_dfs[i].index.name = 'record_id'
                        
                        self.context['data'].index = df_result.index
                        self.context['data'].index.name = 'record_id'

                    # Non-Trivial Validation: by default, a stage may only return
                    # indices from the current survivor universe.
                    allow_new_indices = bool(stage_cfg.get("allow_new_indices", False))
                    if not df_result.index.isin(self.context['data'].index).all():
                        if not allow_new_indices:
                            raise ValueError(
                                f"Critical Integrity Error in stage '{stage_cfg['name']}': "
                                f"Stage introduced new indices not present in the current survivor universe."
                            )

                        expanded_index = self.context['data'].index.union(df_result.index)
                        self.context['data'] = self.context['data'].reindex(expanded_index)

                    # Merge stage outputs into context so downstream stages can
                    # consume derived features (e.g. split flags, recoded targets).
                    if not df_result.empty and len(df_result.columns) > 0:
                        for col in df_result.columns:
                            self.context['data'].loc[df_result.index, col] = df_result[col]

                    accumulated_dfs.append(df_result)
                    last_stage_df = df_result
                    
                    # Stage-wise Initialization (Waterfall Filtering):
                    # Downstream stages only see records that 'survived' this stage.
                    # This ensures sequential dependencies are respected.
                    self.context['data'] = self.context['data'].loc[df_result.index]
                    survivor_pct = (len(self.context['data']) / input_count) * 100
                    print(f"   📉 Waterfall Update: {len(self.context['data'])} survivors ({survivor_pct:.1f}%)")

            else:
                print(f"⚠️ Warning: Method '{method_name}' not found in featurization.py. Skipping stage.")

        if not accumulated_dfs:
            print("⚠️ No data accumulated from pipeline stages.")
            return pd.DataFrame()

        # Horizontal concatenation aligned by the Index.
        # Records dropped by previous stages will naturally result in NaN 
        # values for columns generated in subsequent stages.
        final_df = pd.concat(accumulated_dfs, axis=1)
        
        # (5) Finalize and Persist
        final_df = final_df.sort_index(ascending=True)
        
        output_path = resolver.featurized_dataset_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_df.to_csv(output_path, index=False)

        print(f"✅ Pipeline complete. Resulting dataset shape: {final_df.shape}")
        print(f"💾 Featurized data persisted to: {output_path}")

        # Persist model-ready export derived from final stage output.
        if last_stage_df is not None and not last_stage_df.empty:
            model_ready_df = last_stage_df.copy()
            if resolver.model_ready_numeric_only:
                model_ready_df = model_ready_df.select_dtypes(include=["number", "bool"]).copy()

            model_ready_df = model_ready_df.sort_index(ascending=True)
            model_ready_path = resolver.model_ready_dataset_path
            os.makedirs(os.path.dirname(model_ready_path), exist_ok=True)
            model_ready_df.to_csv(model_ready_path, index=False)
            print(f"💾 Model-ready data persisted to: {model_ready_path}")

        return final_df