import pandas as pd
import importlib
import os
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

from tabular.modeling_filter import drop_leakage_prone_columns


def infer_top_k_from_importances(
    importances: pd.Series,
    mode: str = "fixed",
    fixed_top_k: int = 50,
    min_k: int = 1,
    min_ratio: float = 0.0,
    min_feature_count: int = 0,
    max_k: int = 0,
    target_feature_count: int = 0,
    kneedle_sensitivity: float = 1.0,
    kneedle_curve: str = "convex",
    kneedle_direction: str = "decreasing",
    require_kneedle: bool = False,
) -> int:
    """Returns the feature-count cap using fixed or kneedle-style elbow detection."""
    n = int(len(importances))
    if n <= 0:
        return 0

    ratio_floor = int((float(min_ratio) * float(n)) + 0.999999)
    lower = max(1, int(min_k), int(min_feature_count), ratio_floor)
    upper = int(max_k)
    if upper <= 0:
        upper = n
    upper = max(lower, min(upper, n))

    selection_mode = str(mode).strip().lower()
    if int(target_feature_count) > 0:
        target = int(target_feature_count)
        if upper <= 0:
            upper = n
        return max(1, min(target, upper))

    if selection_mode != "kneedle":
        k = int(fixed_top_k)
        if k <= 0:
            k = n
        return max(lower, min(k, upper))

    x = list(range(1, n + 1))
    y = pd.to_numeric(importances, errors="coerce").fillna(0.0).to_numpy()

    knee_value = None
    try:
        kneed_module = importlib.import_module("kneed")
        KneeLocator = kneed_module.KneeLocator

        locator = KneeLocator(
            x,
            y,
            curve=str(kneedle_curve).strip().lower(),
            direction=str(kneedle_direction).strip().lower(),
            S=float(kneedle_sensitivity),
        )
        knee_value = locator.knee
    except Exception as exc:
        if require_kneedle:
            raise RuntimeError(
                "KneeLocator is required for FEATURE_SELECTION_TOP_K_MODE='kneedle' but is unavailable. "
                "This suggests weak or unstable feature-importance structure; run a manual feature-selection "
                "experiment to validate cutoff behavior."
            ) from exc
        knee_value = None

    if knee_value is None:
        if require_kneedle:
            raise RuntimeError(
                "KneeLocator did not find a stable elbow for feature importances. "
                "Feature quality may be poor; run a manual experiment to verify feature cutoff."
            )
        if n <= 2:
            inferred = n
        else:
            y_min = float(y.min())
            y_max = float(y.max())
            if y_max == y_min:
                inferred = n
            else:
                y_norm = (y - y_min) / (y_max - y_min)
                x_norm = pd.Series(x, dtype="float64")
                x_norm = ((x_norm - x_norm.min()) / (x_norm.max() - x_norm.min())).to_numpy()

                x0, y0 = x_norm[0], y_norm[0]
                x1, y1 = x_norm[-1], y_norm[-1]

                denominator = ((y1 - y0) ** 2 + (x1 - x0) ** 2) ** 0.5
                if denominator == 0:
                    inferred = n
                else:
                    distances = abs((y1 - y0) * x_norm - (x1 - x0) * y_norm + x1 * y0 - y1 * x0) / denominator
                    inferred = int(distances.argmax()) + 1
    else:
        inferred = int(knee_value)

    if fixed_top_k > 0:
        inferred = min(inferred, int(fixed_top_k))

    return max(lower, min(int(inferred), upper))


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
            xgboost_module = importlib.import_module("xgboost")
            XGBClassifier = xgboost_module.XGBClassifier
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
    exclude_candidate_name_patterns: tuple[str, ...] | list[str] | None = None,
    top_k_mode: str = "fixed",
    top_k_min: int = 1,
    top_k_min_ratio: float = 0.0,
    min_feature_count: int = 0,
    top_k_max: int = 0,
    target_feature_count: int = 0,
    kneedle_sensitivity: float = 1.0,
    kneedle_curve: str = "convex",
    kneedle_direction: str = "decreasing",
    require_kneedle: bool = False,
    diagnostics_out: dict | None = None,
) -> list[str]:
    """Selects model features using threshold or tree-ensemble importance."""
    if train_df is None or train_df.empty:
        return []
    if target_col not in train_df.columns:
        raise KeyError(f"Required target column '{target_col}' not found in train data.")

    safe_train_df = drop_leakage_prone_columns(
        data=train_df,
        patterns=exclude_candidate_name_patterns,
        keep_cols=[target_col],
    )

    eligible: list[str] = []
    n_rows = len(safe_train_df)
    for col in candidate_cols:
        if col == target_col:
            continue
        if col not in safe_train_df.columns:
            continue

        non_null_rate = float(safe_train_df[col].notna().sum()) / float(n_rows)
        n_unique = int(safe_train_df[col].nunique(dropna=True))

        if non_null_rate >= float(min_non_null_rate) and n_unique >= int(min_unique):
            eligible.append(col)

    if not eligible:
        return []

    selection_method = str(method).lower().strip()
    if selection_method != "tree_ensemble":
        return eligible

    X = _encode_for_tree_model(safe_train_df, eligible)
    y = pd.to_numeric(safe_train_df[target_col], errors="coerce").fillna(0).astype(int)

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

    k = infer_top_k_from_importances(
        importances=filtered,
        mode=top_k_mode,
        fixed_top_k=top_k,
        min_k=top_k_min,
        min_ratio=top_k_min_ratio,
        min_feature_count=min_feature_count,
        max_k=top_k_max,
        target_feature_count=target_feature_count,
        kneedle_sensitivity=kneedle_sensitivity,
        kneedle_curve=kneedle_curve,
        kneedle_direction=kneedle_direction,
        require_kneedle=require_kneedle,
    )
    if k > 0:
        filtered = filtered.head(int(k))

    if diagnostics_out is not None:
        diagnostics_out["importance_series"] = importances.copy()
        diagnostics_out["filtered_importance_series"] = filtered.copy()
        diagnostics_out["selected_k"] = int(k)
        diagnostics_out["min_feature_count"] = int(min_feature_count)
        diagnostics_out["target_feature_count"] = int(target_feature_count)
        diagnostics_out["knee_target_count"] = int(target_feature_count)
        diagnostics_out["top_k_mode"] = str(top_k_mode)

    return filtered.index.tolist()


def plot_feature_selection_knee_curve(
    importance_series: pd.Series,
    selected_k: int,
    output_path: str,
    title: str = "Feature Importance Knee Curve",
) -> str:
    """Plots and saves the ranked importance knee curve as a PNG image."""
    if importance_series is None or importance_series.empty:
        raise ValueError("Cannot plot knee curve: importance_series is empty.")

    importances = pd.to_numeric(importance_series, errors="coerce").fillna(0.0)
    ranks = list(range(1, len(importances) + 1))

    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        raise RuntimeError(
            "matplotlib is required to generate knee-curve plots. Install matplotlib and rerun."
        ) from exc

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(ranks, importances.values, marker="o", linewidth=1.5, markersize=3)

    k = int(selected_k)
    if 1 <= k <= len(importances):
        ax.axvline(x=k, linestyle="--", linewidth=1.2)
        ax.scatter([k], [float(importances.iloc[k - 1])], s=60, zorder=3)
        ax.text(k, float(importances.iloc[k - 1]), f"  k={k}", va="bottom")

    ax.set_title(title)
    ax.set_xlabel("Ranked Feature Index")
    ax.set_ylabel("Importance")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


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
