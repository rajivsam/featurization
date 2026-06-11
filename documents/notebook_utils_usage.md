# Notebook Utility Usage

This document shows a simple Jupyter notebook excerpt for retrieving featurization artifacts from the package using a workspace `working_dir`.

## Goal

Use the package notebook utilities to resolve and load:
- `featurized_data.csv`
- `model_ready_numeric_data.csv`
- `feature_selection_knee_curve.png`

### Example Notebook Excerpt

```python
# 1) Import the notebook helpers and filesystem utilities
import os
from featurization.notebook_utils import (
    build_notebook_resolver,
    get_featurization_artifact_paths,
    get_featurization_artifact_status,
    load_featurized_dataset,
    load_model_ready_dataset,
)

# 2) Launch the notebook from the project's notebooks directory
notebook_dir = os.getcwd()

# 3) Build a PathCoordinator from the notebook directory
resolver = build_notebook_resolver(notebook_dir)

# 4) Resolve artifact paths
artifact_paths = get_featurization_artifact_paths(resolver)
print("Artifact paths:")
for name, path in artifact_paths.items():
    print(f"- {name}: {path}")

# 5) Check artifact presence on disk
artifact_status = get_featurization_artifact_status(resolver)
print("Artifact status:")
for name, info in artifact_status.items():
    print(f"- {name}: exists={info['exists']} path={info['path']}")

# 6) Load generated CSV outputs
featurized_df = load_featurized_dataset(resolver)
model_ready_df = load_model_ready_dataset(resolver)

print("Featurized dataset shape:", featurized_df.shape)
print("Model-ready dataset shape:", model_ready_df.shape)

# 7) Access the knee curve PNG path for display or inspection
knee_curve_path = artifact_paths["feature_selection_knee_curve_path"]
print("Knee curve path:", knee_curve_path)
```

## Notebook Cell Example

```xml
<VSCode.Cell language="markdown">
This notebook is launched from the `notebooks/` directory. It resolves the parent workspace root, reads `featurizer_config.yaml`, and locates the generated featurization artifacts.
</VSCode.Cell>
<VSCode.Cell language="python">
import os
from featurization.notebook_utils import (
    build_notebook_resolver,
    get_featurization_artifact_paths,
    get_featurization_artifact_status,
    load_featurized_dataset,
    load_model_ready_dataset,
)

notebook_dir = os.getcwd()
resolver = build_notebook_resolver(notebook_dir)

artifact_paths = get_featurization_artifact_paths(resolver)
print(artifact_paths)

artifact_status = get_featurization_artifact_status(resolver)
print(artifact_status)

featurized_df = load_featurized_dataset(resolver)
model_ready_df = load_model_ready_dataset(resolver)
print("featurized", featurized_df.shape)
print("model ready", model_ready_df.shape)

print("knee curve:", artifact_paths["feature_selection_knee_curve_path"])
</VSCode.Cell>
```

## Notes

- The notebook assumes it is launched from the `notebooks` directory.
- `build_notebook_resolver` checks the notebook parent directory for `featurizer_config.yaml`.
- If the config file is missing, it raises `FileNotFoundError` with a clear message:
  - "This does not appear to be a kmds-featurization workspace."
- `load_featurized_dataset` and `load_model_ready_dataset` raise `FileNotFoundError` if the expected CSV is missing.
- The knee curve path points to the PNG file under the featurization output directory.
