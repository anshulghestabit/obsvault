# src/features/build_features.py

import pandas as pd


# ======================================================
# Feature Builders
# ======================================================

def _add_total_sf(df: pd.DataFrame) -> pd.DataFrame:
    df["TotalSF"] = (
        df["TotalBsmtSF"]
        + df["1stFlrSF"]
        + df["2ndFlrSF"]
    )
    return df


def _add_total_bathrooms(df: pd.DataFrame) -> pd.DataFrame:
    df["TotalBathrooms"] = (
        df["FullBath"]
        + 0.5 * df["HalfBath"]
        + df["BsmtFullBath"]
        + 0.5 * df["BsmtHalfBath"]
    )
    return df


def _add_house_age(df: pd.DataFrame) -> pd.DataFrame:
    df["HouseAge"] = df["YrSold"] - df["YearBuilt"]
    return df


def _add_remodel_age(df: pd.DataFrame) -> pd.DataFrame:
    df["RemodelAge"] = df["YrSold"] - df["YearRemodAdd"]
    return df


def _add_is_remodeled(df: pd.DataFrame) -> pd.DataFrame:
    df["IsRemodeled"] = (
        df["YearRemodAdd"] != df["YearBuilt"]
    ).astype(int)
    return df


def _add_total_porch_sf(df: pd.DataFrame) -> pd.DataFrame:
    df["TotalPorchSF"] = (
        df["OpenPorchSF"]
        + df["EnclosedPorch"]
        + df["3SsnPorch"]
        + df["ScreenPorch"]
    )
    return df


def _add_total_outdoor_sf(df: pd.DataFrame) -> pd.DataFrame:
    df["TotalOutdoorSF"] = (
        df["WoodDeckSF"]
        + df["TotalPorchSF"]
    )
    return df


def _add_has_garage(df: pd.DataFrame) -> pd.DataFrame:
    df["HasGarage"] = (df["GarageCars"] > 0).astype(int)
    return df


def _add_has_basement(df: pd.DataFrame) -> pd.DataFrame:
    df["HasBasement"] = (df["TotalBsmtSF"] > 0).astype(int)
    return df


def _add_quality_index(df: pd.DataFrame) -> pd.DataFrame:
    df["QualityIndex"] = (
        df["OverallQual"] * df["OverallCond"]
    )
    return df


# ======================================================
# Public API
# ======================================================

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies all feature engineering steps.
    Returns new dataframe with engineered features.
    """

    df = df.copy()

    feature_pipeline = [
        _add_total_sf,
        _add_total_bathrooms,
        _add_house_age,
        _add_remodel_age,
        _add_is_remodeled,
        _add_total_porch_sf,
        _add_total_outdoor_sf,
        _add_has_garage,
        _add_has_basement,
        _add_quality_index,
    ]

    for func in feature_pipeline:
        df = func(df)

    return df