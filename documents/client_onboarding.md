# Client Onboarding for `kmds-featurization`

This document explains how a package consumer can initialize a Copilot orchestrator to use `kmds-featurization`.

## Step 1: Install the package

Install the package using your normal Python packaging workflow.

```bash
pip install kmds-featurization
```

If you are working from source in a local repository, install in editable mode:

```bash
pip install -e .
```

## Step 2: Discover package entry points and commands

Use the package discovery API to learn the supported CLI commands and package metadata.

```python
from featurization import get_package_info, get_cli_command_names

info = get_package_info()
print(info)

commands = get_cli_command_names()
print(commands)
```

This will return:

- `package_name`: package identifier
- `version`: installed version
- `entry_point`: the shell CLI command
- `cli_commands`: supported CLI actions
- `documentation_note`: current guidance about package docs

## Step 3: Initialize the operating workspace

The primary workflow is driven through the CLI.

```bash
featurization-cli init --working-dir /path/to/workspace \
  --metadata-file /path/to/metadata.csv \
  --data-file /path/to/data.csv
```

This creates the workspace configuration file and anchors the metadata and cleaned data paths.

## Step 4: Bootstrap a starter configuration

If you need a provisional config file before running a full init, use:

```bash
featurization-cli bootstrap --working-dir /path/to/workspace \
  --metadata-file your_metadata.csv \
  --data-file your_cleaned_data.csv
```

## Step 5: Run the pipeline

Once the workspace is initialized, execute the pipeline with:

```bash
featurization-cli run --working-dir /path/to/workspace
```

## Step 6: Use the feature advisor

If you want model-aware feature guidance, call the advisor:

```bash
featurization-cli advise --working-dir /path/to/workspace --model-intent catboost
```

## Step 7: Interpret package metadata from clients

A client orchestrator can auto-configure itself by using `get_package_info()`:

```python
from featurization import get_package_info
info = get_package_info()

# Use info['cli_commands'] to configure supported steps
if 'init' in info['cli_commands']:
    print('Workspace init is supported')
```

## Notes

- This package no longer ships installed internal documents. Use this repository's top-level `documents/` folder for onboarding and implementation guidance.
- The package discovery API is the supported runtime entrypoint for clients.
