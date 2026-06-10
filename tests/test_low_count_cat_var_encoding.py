import pandas as pd

from tabular.low_count_cat_var_encoding import get_categorical_subset


class _Loader:
    def __init__(self, metadata: pd.DataFrame):
        self.metadata = metadata


def test_get_categorical_subset_uses_or_logic_between_metadata_and_dtype():
    data = pd.DataFrame(
        {
            "id": [1, 2],
            "status_code": [10, 20],
            "industry": ["retail", "food"],
            "amount": [100.0, 200.0],
        }
    )
    metadata = pd.DataFrame(
        {
            "attribute_name": ["status_code", "amount"],
            "logical_type": ["categorical", "numeric"],
        }
    )

    context = {"data": data, "loader": _Loader(metadata)}
    subset = get_categorical_subset(context)

    # status_code comes from metadata logical categorical (even though it's int)
    # industry comes from pandas object dtype (even if not tagged categorical in metadata)
    assert subset.columns.tolist() == ["status_code", "industry"]


def test_get_categorical_subset_respects_drop_filter_case_insensitive():
    data = pd.DataFrame(
        {
            "Status_Code": [10, 20],
            "industry": ["retail", "food"],
        }
    )
    metadata = pd.DataFrame(
        {
            "attribute_name": ["status_code"],
            "logical_type": ["categorical"],
        }
    )

    context = {"data": data, "loader": _Loader(metadata)}
    subset = get_categorical_subset(context, drop_filter=["STATUS_CODE"])

    assert subset.columns.tolist() == ["industry"]
