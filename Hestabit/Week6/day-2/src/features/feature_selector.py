# src/features/feature_selector.py

import json
import numpy as np
import pandas as pd

from sklearn.feature_selection import mutual_info_regression, RFE
from sklearn.ensemble import RandomForestRegressor


# ======================================================
# Correlation Filter
# ======================================================

def remove_high_correlation(
    X: pd.DataFrame,
    threshold: float = 0.9
):

    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    to_drop = [
        column for column in upper.columns
        if any(upper[column] > threshold)
    ]

    return X.drop(columns=to_drop), to_drop


# ======================================================
# Mutual Information
# ======================================================

def select_by_mutual_information(
    X: pd.DataFrame,
    y: pd.Series,
    top_k: int = 40
):

    mi = mutual_info_regression(X, y, random_state=42)
    mi_series = pd.Series(mi, index=X.columns)
    mi_series = mi_series.sort_values(ascending=False)

    selected = mi_series.head(top_k).index.tolist()

    return selected, mi_series


# ======================================================
# RFE
# ======================================================

def select_by_rfe(
    X: pd.DataFrame,
    y: pd.Series,
    n_features: int = 30
):

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    rfe = RFE(
        estimator=model,
        n_features_to_select=n_features
    )

    rfe.fit(X, y)

    selected = X.columns[rfe.support_].tolist()

    return selected


# ======================================================
# Master Function
# ======================================================

def select_features(
    X: pd.DataFrame,
    y: pd.Series,
    correlation_threshold: float = 0.9,
    mi_top_k: int = 40,
    rfe_n_features: int = 30,
    save_path: str = "src/features/feature_list.json"
):

    # Step 1: Correlation filtering
    X_corr, dropped_corr = remove_high_correlation(
        X,
        threshold=correlation_threshold
    )

    # Step 2: Mutual Information
    mi_selected, mi_scores = select_by_mutual_information(
        X_corr,
        y,
        top_k=mi_top_k
    )

    # Step 3: RFE
    rfe_selected = select_by_rfe(
        X_corr,
        y,
        n_features=rfe_n_features
    )

    # Step 4: Intersection
    final_selected = list(
        set(mi_selected).intersection(set(rfe_selected))
    )

    if len(final_selected) == 0:
        final_selected = rfe_selected

    feature_dict = {
        "all_features": X.columns.tolist(),
        "correlation_filtered": X_corr.columns.tolist(),
        "dropped_by_correlation": dropped_corr,
        "mi_selected": mi_selected,
        "rfe_selected": rfe_selected,
        "final_selected": final_selected
    }

    with open(save_path, "w") as f:
        json.dump(feature_dict, f, indent=4)

    return final_selected, mi_scores