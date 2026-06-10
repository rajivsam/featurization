## 📑 KMDS Packaged State Stash: Platform Path Abstraction Feature Only

## 📌 Core Architectural Design Rules

To ensure total alignment with the unified platform framework across all modules (`dd-parser-cleaner`, `featurization`, etc.), all packages must completely eliminate manual path manipulation utilities like `os.path.join(self.working_dir, ...)` [1.1]. Instead, they must delegate pathing calculations to a common instance model interface matching the layout specification below [1.1].

## 📂 Unified Directory Blueprint Mapping

* Raw Processing Payloads Input Data Target Directory: `{working_dir}/data/`
* Downstream Ingestion Engine Result Output Directory: `{working_dir}/data/dd_cleaner_results/`
* Inferred Mapping Signature Dictionary Output Directory: `{working_dir}/data_dictionary/dd_analysis_results/`
* Markdown Status Analytics Summary Report Directory: `{working_dir}/documents/`

---

## 📄 1. Enforced Abstraction Module (`src/path_coordinator.py`)

```python
importos
fromtypingimportDict, Any

classPlatformPathResolver:
    """
    Encapsulates structural pipeline layout constants.
    Guarantees runtime modules and test clients conform to the same directory rules.
    """
    def__init__(self, working_dir: str, config: Dict[str, Any]):
        self.working_dir = os.path.abspath(working_dir)
        self.config = config

    @property
    defraw_data_input_path(self) -> str:
        """Enforces that raw data files live strictly inside the data/ folder."""
        filename = self.config.get("raw_dataset_file", "sba_loans_raw.csv")
        return os.path.join(self.working_dir, "data", filename)

    @property
    defdata_dictionary_dir(self) -> str:
        """Resolves target data dictionary folder destinations."""
        raw_dir = self.config.get("dd_parser_output_dir", "dd_analysis_results")
        target_dir = os.path.join(self.working_dir, "data_dictionary", raw_dir)
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    @property
    defdata_dictionary_csv_path(self) -> str:
        """Resolves the absolute path to the data dictionary CSV output file."""
        filename = self.config.get("output_filename", "sba_analysis_results.csv")
        return os.path.join(self.data_dictionary_dir, filename)

    @property
    defdata_cleaner_dir(self) -> str:
        """Resolves target data cleaner folder destinations inside data/."""
        raw_dir = self.config.get("dd_cleaner_output_dir", "dd_cleaner_results")
        target_dir = os.path.join(self.working_dir, "data", raw_dir)
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    @property
    defdocuments_dir(self) -> str:
        """Forces analytical markdown deliverables straight into documents/."""
        raw_dir = self.config.get("documents_dir", "documents")
        target_dir = os.path.join(self.working_dir, raw_dir)
        os.makedirs(target_dir, exist_ok=True)
        return target_dir
```

---

## 📄 2. Distribution Wheel Registry Inclusions (`pyproject.toml`)

To allow flat utility modules to compile seamlessly alongside core folder directories inside Hatch without throwing runtime `ImportError` exceptions, add the explicit `include` hook [3.1]:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/dd_parser", "src/dd_cleaner"]
include = [
    "src/path_coordinator.py"
]
```

---

## 🛠️ Verification Checklist for Next-Stage Modules

* No Path Hardcoding: All file target reads and writes check properties directly from `PlatformPathResolver` variables [1.1].
* Consistent Signatures: Harness test setups and analytics summary writers ingest coordinates from the exact same abstraction instance layout, guaranteeing zero context drift [1.1].

---

Enjoy your well-deserved milestone success! Whenever you are ready to expand this framework into your downstream Featurization module components, just reference this state stash, and we can begin drafting the architectural layout rules right away!
