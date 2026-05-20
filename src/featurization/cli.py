import argparse
import sys
import os
from featurization.engine import FeaturizationService

def main():
    parser = argparse.ArgumentParser(
        description="Featurization Service Shell - kmds-data-helper Ecosystem"
    )
    parser.add_argument(
        "--working-dir", 
        type=str, 
        required=True, 
        help="Path to the active project working directory containing configurations and datasets."
    )
    parser.add_argument(
        "--target-col", 
        type=str, 
        default="target", 
        help="Name of the machine learning target prediction column."
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml", 
        help="Path to the environment config layout file."
    )

    args = parser.parse_args()

    if not os.path.isdir(args.working_dir):
        print(f"❌ Error: Provided working directory does not exist: {args.working_dir}")
        sys.exit(1)

    try:
        # Initialize synchronized service abstraction
        service = FeaturizationService(working_dir=args.working_dir, config_path=args.config)
        service.orchestrate_pipeline(target_column=args.target_col)
        print("✅ Pipeline core shell verification step complete.")
    except Exception as e:
        print(f"💥 Pipeline Execution Failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
