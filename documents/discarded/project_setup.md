The `featurization` package follows a modular, configuration-driven layout similar to the `dd-parser-cleaner` ecosystem. It is designed to ingest clean data from `dd_cleaner` and produce model-ready feature matrices.

## 📂 Workspace Directory Layout

A standard `src/` layout is recommended for library code that will be packaged and distributed, as it ensures tests import the installed package correctly. [1]

```text
/home/rajiv/programming/featurization/     # New Workspace Directory
├── pyproject.toml                         # Project distribution and CLI registry
├── config.yaml                            # Feature engineering parameters & recipes
├── README.md                              # Project overview and documentation
└── src/
    └── featurization/                     # Package source code
        ├── __init__.py                    # Marks directory as an importable package
        ├── cli.py                         # Entry point: `compute-features`
        ├── engine.py                      # Main orchestration engine
        ├── registry.py                    # Feature transform registration mechanism
        └── transforms/                    # Specialized transformation modules
            ├── __init__.py
            ├── numeric.py                 # Scaling and log transforms
            ├── categorical.py             # Geographical and frequency encoding
            └── datetime.py                # Time-series intervals and seasonality
```

## ⚙️ Dependencies and Metadata (`pyproject.toml`)

The `pyproject.toml` file centralizes project metadata, dependencies, and build specifications. It uses the `hatchling` build backend for modern packaging standards. [2, 3]

```toml
[project]
name = "featurization"
version = "0.1.0"
description = "A configuration-driven feature engineering engine reading from dd-cleaner payloads."
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.2.0",      # Data manipulation and cleaning
    "numpy>=1.26.0",       # Fundamental numerical computation
    "pyyaml>=6.0.1",      # Configuration file parsing
    "scikit-learn>=1.4.0", # Standard ML scaling and encoding
]

[projectscripts]
compute-features = "featurization.cli:main"# CLI entry point

[build-system]
requires = ["hatchling"] # Advanced build-backend
build-backend = "hatchling.build"

[toolhatchbuildtargetswheel]
packages = ["src/featurization"]
```

## 🛠️ Core Functional Components

* `engine.py`: Orchestrates the data flow by reading clean CSVs from `dd_cleaner` and applying recipes defined in `config.yaml`.
* `registry.py`: Tracks available transformation functions, allowing them to be applied dynamically based on column types or explicit configuration.
* `transforms/`: Contains atomic mathematical rules for processing different data types, such as handling high-cardinality geographical fields or scaling numeric distributions. [4]

Does this structural map align with your expectations for the next implementation phase?

[1] [https://realpython.com](https://realpython.com/ref/best-practices/project-layout/)

[2] [https://github.com](https://github.com/microsoft/python-package-template)

[3] [https://drivendata.co](https://drivendata.co/blog/python-packaging-2023)

[4] [https://medium.com](https://medium.com/@CodeWithHannan/top-15-python-packages-for-machine-learning-projects-bdefad096a27)
