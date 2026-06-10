import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier


def _encode_for_tree_model(train_df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """Encodes mixed dtypes into a numeric frame suitable for tree models."""
    encoded = pd.DataFrame(index=train_df.index)

    for col in feature_cols:
        series = train_df[col]
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            encoded[col] = pd.to_numeric(series, errors="coerce")
            continue

        codes, _ = pd.factorize(series.astype("string"), sort=False)
        encoded[col] = pd.Series(codes, index=series.index).replace(-1, pd.NA)

    return encoded.fillna(-999.0)


def _build_tree_selector(
    tree_model: str,
    n_estimators: int,
    learning_rate: float,
    max_depth: int,
    subsample: float,
    random_state: int,
):
    """Builds a tree-based selector model from config values."""
    model_name = str(tree_model).lower().strip()

    if model_name == "random_forest":
        return RandomForestClassifier(
            n_estimators=int(n_estimators),
            max_depth=int(max_depth),
            random_state=int(random_state),
            n_jobs=-1,
        )

    if model_name == "xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError as exc:
            raise ImportError(
                "FEATURE_SELECTION_TREE_MODEL is set to 'xgboost' but xgboost is not installed. "
                "Install xgboost or set FEATURE_SELECTION_TREE_MODEL to 'gbm' or 'random_forest'."
            ) from exc

        return XGBClassifier(
            n_estimators=int(n_estimators),
            learning_rate=float(learning_rate),
            max_depth=int(max_depth),
            subsample=float(subsample),
            random_state=int(random_state),
            objective="binary:logistic",
            eval_metric="logloss",
            n_jobs=-1,
        )

    return GradientBoostingClassifier(
        n_estimators=int(n_estimators),
        learning_rate=float(learning_rate),
        max_depth=int(max_depth),
        subsample=float(subsample),
        random_state=int(random_state),
    )


def select_model_features(
    train_df: pd.DataFrame,
    candidate_cols: list[str],
    target_col: str,
    min_non_null_rate: float = 0.01,
    min_unique: int = 2,
    method: str = "threshold",
    top_k: int = 50,
    importance_floor: float = 0.0,
    tree_model: str = "gbm",
    tree_n_estimators: int = 200,
    tree_learning_rate: float = 0.05,
    tree_max_depth: int = 3,
    tree_subsample: float = 0.8,
    tree_random_state: int = 42,
) -> list[str]:
    """Selects model features using threshold or tree-ensemble importance."""
    if train_df is None or train_df.empty:
        return []
    if target_col not in train_df.columns:
        raise KeyError(f"Required target column '{target_col}' not found in train data.")

    eligible: list[str] = []
    n_rows = len(train_df)
    for col in candidate_cols:
        if col not in train_df.columns:
            continue

        non_null_rate = float(train_df[col].notna().sum()) / float(n_rows)
        n_unique = int(train_df[col].nunique(dropna=True))

        if non_null_rate >= float(min_non_null_rate) and n_unique >= int(min_unique):
            eligible.append(col)

    if not eligible:
        return []

    selection_method = str(method).lower().strip()
    if selection_method != "tree_ensemble":
        return eligible

    X = _encode_for_tree_model(train_df, eligible)
    y = pd.to_numeric(train_df[target_col], errors="coerce").fillna(0).astype(int)

    selector = _build_tree_selector(
        tree_model=tree_model,
        n_estimators=tree_n_estimators,
        learning_rate=tree_learning_rate,
        max_depth=tree_max_depth,
        subsample=tree_subsample,
        random_state=tree_random_state,
    )
    selector.fit(X, y)

    importances = pd.Series(selector.feature_importances_, index=eligible)
    importances = importances.sort_values(ascending=False)

    filtered = importances[importances >= float(importance_floor)]
    if filtered.empty:
        filtered = importances

    k = int(top_k)
    if k > 0:
        filtered = filtered.head(k)

    return filtered.index.tolist()


def project_feature_space(
    data: pd.DataFrame,
    feature_cols: list[str],
    fill_value: float = 0.0,
) -> pd.DataFrame:
    """Projects data into an exact feature schema, filling missing columns."""
    if data is None or data.empty:
        return pd.DataFrame(columns=feature_cols)

    projected = data.reindex(columns=feature_cols)
    return projected.fillna(fill_value)
