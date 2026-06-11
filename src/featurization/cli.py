import argparse
import sys
import os
import yaml
from featurization.core.sequential_pipeline_runner import PipelineRunner
from featurization.core.featurization_init import (
    initialize_config,
    bootstrap_provisional_config,
)
from featurization.core.path_coordinator import PathCoordinator

def main():
    parser = argparse.ArgumentParser(
        description="Featurization Service Shell - kmds-data-helper Ecosystem"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Init Command ---
    init_parser = subparsers.add_parser("init", help="Initialize a featurization workspace configuration.")
    init_parser.add_argument(
        "--working-dir", 
        required=True, 
        help="Path to the workflow directory."
    )
    init_parser.add_argument(
        "--metadata-file", 
        required=True, 
        help="The dd-parser-cleaner summary CSV filename."
    )
    init_parser.add_argument(
        "--data-file", 
        required=True, 
        help="The cleaned data CSV filename."
    )
    init_parser.add_argument(
        "--structural-type",
        choices=["cross-sectional", "longitudinal", "panel"],
        default="cross-sectional",
        help="The structural type of the dataset (cross-sectional, longitudinal, or panel)."
    )

    # --- Add-Stage Command ---
    add_parser = subparsers.add_parser("add-stage", help="Add a custom stage to the pipeline.")
    add_parser.add_argument("--name", required=True, help="Name of the stage.")
    add_parser.add_argument("--entity", required=True, help="Entity category in metadata (e.g., geographical).")
    add_parser.add_argument("--sub-filter", required=True, help="Specific sub-filter group (e.g., Borrower).")
    add_parser.add_argument("--config", default="featurizer_config.yaml", help="Config filename.")

    # --- Check Command ---
    check_parser = subparsers.add_parser("check", help="Check if a stage is configured.")
    check_parser.add_argument("--name", required=True, help="Stage name to verify.")
    check_parser.add_argument("--config", default="featurizer_config.yaml", help="Config filename.")

    # --- Bootstrap Command ---
    bootstrap_parser = subparsers.add_parser(
        "bootstrap", help="Create a provisional starter featurization config file."
    )
    bootstrap_parser.add_argument(
        "--working-dir",
        required=True,
        help="Path to the workflow directory where the provisional config will be written."
    )
    bootstrap_parser.add_argument(
        "--config-name",
        default="provisional_featurization_config.yaml",
        help="Filename for the provisional configuration YAML."
    )
    bootstrap_parser.add_argument(
        "--metadata-file",
        default="your_metadata.csv",
        help="Placeholder metadata filename for the starter config."
    )
    bootstrap_parser.add_argument(
        "--data-file",
        default="your_cleaned_data.csv",
        help="Placeholder cleaned data filename for the starter config."
    )
    bootstrap_parser.add_argument(
        "--structural-type",
        choices=["cross-sectional", "longitudinal", "panel"],
        default="cross-sectional",
        help="Structural type placeholder for the starter config."
    )
    bootstrap_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing provisional config if it already exists."
    )

    # --- Run Command ---
    run_parser = subparsers.add_parser("run", help="Execute the featurization pipeline.")
    run_parser.add_argument(
        "--working-dir", 
        type=str, 
        required=True, 
        help="Path to the active project working directory containing configurations and datasets."
    )
    run_parser.add_argument(
        "--target-col", 
        type=str, 
        default="target", 
        help="Name of the machine learning target prediction column."
    )
    run_parser.add_argument(
        "--config", 
        type=str, 
        default="featurizer_config.yaml", 
        help="Path to the environment config layout file."
    )

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "init":
            if not os.path.isdir(args.working_dir):
                print(f"❌ Error: Provided working directory does not exist: {args.working_dir}")
                sys.exit(1)
            initialize_config(
                args.working_dir, 
                args.metadata_file, 
                args.data_file, 
                args.structural_type
            )
            print("✅ Initialization Complete.")
            return

        if args.command == "bootstrap":
            if not os.path.isdir(args.working_dir):
                os.makedirs(args.working_dir, exist_ok=True)
            try:
                config_path = bootstrap_provisional_config(
                    args.working_dir,
                    metadata_file=args.metadata_file,
                    data_file=args.data_file,
                    structural_type=args.structural_type,
                    config_name=args.config_name,
                    overwrite=args.overwrite,
                )
                print(f"✅ Provisional config written: {config_path}")
            except FileExistsError as exc:
                print(f"❌ {exc}")
                sys.exit(1)
            return

        if args.command == "check":
            if not os.path.exists(args.config):
                print(f"❌ Config file '{args.config}' not found.")
                sys.exit(1)
            with open(args.config, "r") as f:
                config = yaml.safe_load(f)
            working_dir = config.get("working_dir", os.getcwd())
            resolver = PathCoordinator(working_dir, config)
            
            if resolver.is_stage_configured(args.name):
                print(f"✅ Stage '{args.name}' is configured in the pipeline.")
            else:
                print(f"❌ Stage '{args.name}' is NOT configured.")
                sys.exit(1)
            return

        if args.command == "run":
            # Load configuration
            config_path = os.path.join(args.working_dir, args.config)
            if not os.path.exists(config_path):
                config_path = args.config
                
            if not os.path.exists(config_path):
                print(f"❌ Error: Config file not found at {config_path}")
                sys.exit(1)

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Initialize the runner and execute accumulation
            runner = PipelineRunner(working_dir=args.working_dir, config=config)
            runner.accumulate_stages()
            # runner.accumulate_stages() now handles persistence internally via PathCoordinator
            return
    except Exception as e:
        print(f"💥 Pipeline Execution Failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
