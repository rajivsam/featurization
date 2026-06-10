import pandas as pd


def _mask_left(code: str, mask_count: int, mask_char: str) -> str:
    """Masks mask_count leading characters in code."""
    if mask_count <= 0:
        return code
    if mask_count >= len(code):
        return mask_char * len(code)
    return (mask_char * mask_count) + code[mask_count:]


def _mask_right(code: str, mask_count: int, mask_char: str) -> str:
    """Masks mask_count trailing characters in code."""
    if mask_count <= 0:
        return code
    if mask_count >= len(code):
        return mask_char * len(code)
    return code[: len(code) - mask_count] + (mask_char * mask_count)


def _hierarchical_recode(
    series: pd.Series,
    min_support: int,
    mask_char: str,
    fallback_value: str,
    masker,
) -> pd.Series:
    clean = series.astype("string").fillna("MISSING").str.strip()
    out = pd.Series(index=clean.index, dtype="string")

    base_counts = clean.value_counts(dropna=False)
    supported_codes = set(base_counts[base_counts >= min_support].index.tolist())
    supported_mask = clean.isin(supported_codes)
    out.loc[supported_mask] = clean.loc[supported_mask]

    unresolved_idx = clean.index[~supported_mask]

    for idx in unresolved_idx:
        original = clean.at[idx]
        if not original:
            out.at[idx] = fallback_value
            continue

        resolved_value = None
        code_len = len(original)

        for mask_count in range(1, code_len + 1):
            candidate = masker(original, mask_count, mask_char)

            candidate_series = clean.loc[unresolved_idx].apply(
                lambda x: masker(x, mask_count, mask_char) if x else fallback_value
            )
            candidate_support = int((candidate_series == candidate).sum())

            if candidate_support >= min_support:
                resolved_value = candidate
                break

        out.at[idx] = resolved_value if resolved_value is not None else fallback_value

    return out


def hierarchical_recode_by_support_left(
    series: pd.Series,
    min_support: int,
    mask_char: str = "*",
    fallback_value: str = "OTHERS",
) -> pd.Series:
    """Left-masking variant: 722511 -> *22511 -> **2511 -> ..."""
    return _hierarchical_recode(
        series=series,
        min_support=min_support,
        mask_char=mask_char,
        fallback_value=fallback_value,
        masker=_mask_left,
    )


def hierarchical_recode_by_support_right(
    series: pd.Series,
    min_support: int,
    mask_char: str = "*",
    fallback_value: str = "OTHERS",
) -> pd.Series:
    """Right-masking variant (NAICS-friendly): 722511 -> 72251* -> 7225** -> ..."""
    return _hierarchical_recode(
        series=series,
        min_support=min_support,
        mask_char=mask_char,
        fallback_value=fallback_value,
        masker=_mask_right,
    )


def hierarchical_recode_by_support(
    series: pd.Series,
    min_support: int,
    mask_char: str = "*",
    fallback_value: str = "OTHERS",
) -> pd.Series:
    """
    Recodes low-support values by progressively masking one character from the left
    until the masked representation reaches min_support.

    Example (left-masking):
      722511 -> *22511 -> **2511 -> ...
    """
    return hierarchical_recode_by_support_left(
        series=series,
        min_support=min_support,
        mask_char=mask_char,
        fallback_value=fallback_value,
    )
