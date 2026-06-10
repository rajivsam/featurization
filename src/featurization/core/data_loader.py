import os
import pandas as pd
from featurization.utils import load_kmds_metadata

class KMDSDataLoader:
    """
    Package Component: Centralized data loading module.
    Handles lazy-loading of KMDS datasets and metadata to avoid redundant I/O.
    """
    def __init__(self, resolver):
        self.resolver = resolver
        self._data = None
        self._metadata = None

    @property
    def data(self) -> pd.DataFrame:
        """Lazy-loads the primary cleaned dataset."""
        if self._data is None:
            path = self.resolver.featurization_input_path
            if not os.path.exists(path):
                raise FileNotFoundError(f"Source data not found at: {path}")
            print(f"📥 [Data Loader] Reading cleaned data: {os.path.basename(path)}")
            self._data = pd.read_csv(path, low_memory=False)
        return self._data

    @property
    def metadata(self) -> pd.DataFrame:
        """Lazy-loads the KMDS metadata (data dictionary)."""
        if self._metadata is None:
            path = self.resolver.metadata_path
            if not os.path.exists(path):
                print(f"⚠️ [Data Loader] Metadata missing at {path}. Returning empty frame.")
                self._metadata = pd.DataFrame()
            else:
                print(f"📥 [Data Loader] Reading metadata: {os.path.basename(path)}")
                self._metadata = load_kmds_metadata(path)
        return self._metadata