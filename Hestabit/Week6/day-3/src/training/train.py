import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, KFold, cross_validate
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "final.csv"
MODELS_DIR = BASE_DIR / "models"
EVAL_DIR = BASE_DIR / "evaluation"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    df = pd.read_csv(DATA_PATH)

    if "Id" in df.columns:
        df = df.drop(columns=["Id"])

    if "SalePrice" not in df.columns:
        raise ValueError("Target column 'SalePrice' not found in dataset.")

    X = df.drop(columns=["SalePrice"])
    y = df["SalePrice"]

    return X, y


def build_preprocessor(X):
    numeric_features = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = X.select_dtypes(exclude=["number"]).columns.tolist()

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    return preprocessor


def evaluate_model(name, pipeline, X_train, y_train, X_test, y_test):
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    scoring = {
        "mae": "neg_mean_absolute_error",
        "rmse": "neg_root_mean_squared_error",
        "r2": "r2",
    }

    cv_results = cross_validate(
        pipeline,
        X_train,
        y_train,
        cv=cv,
        scoring=scoring,
        n_jobs=-1,
        return_train_score=False,
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    test_mae = mean_absolute_error(y_test, preds)
    test_rmse = np.sqrt(mean_squared_error(y_test, preds))
    test_r2 = r2_score(y_test, preds)

    return {
        "model_name": name,
        "cv_mae_mean": round(-cv_results["test_mae"].mean(), 4),
        "cv_rmse_mean": round(-cv_results["test_rmse"].mean(), 4),
        "cv_r2_mean": round(cv_results["test_r2"].mean(), 4),
        "test_mae": round(test_mae, 4),
        "test_rmse": round(test_rmse, 4),
        "test_r2": round(test_r2, 4),
        "trained_pipeline": pipeline,
    }


def main():
    X, y = load_data()
    preprocessor = build_preprocessor(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model_dict = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=200, max_depth=None, random_state=42, n_jobs=-1
        ),
        "GradientBoostingRegressor": GradientBoostingRegressor(
            n_estimators=200, learning_rate=0.05, max_depth=3, random_state=42
        ),
    }

    results = {}

    best_model_name = None
    best_pipeline = None
    best_score = float("-inf")

    for name, model in model_dict.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", model),
            ]
        )

        metrics = evaluate_model(name, pipeline, X_train, y_train, X_test, y_test)
        trained_pipeline = metrics.pop("trained_pipeline")
        results[name] = metrics

        if metrics["test_r2"] > best_score:
            best_score = metrics["test_r2"]
            best_model_name = name
            best_pipeline = trained_pipeline

    metrics_output = {
        "best_model": best_model_name,
        "results": results,
    }

    with open(EVAL_DIR / "metrics.json", "w") as f:
        json.dump(metrics_output, f, indent=4)

    joblib.dump(best_pipeline, MODELS_DIR / "best_model.pkl")

    print(f"Best model saved: {best_model_name}")
    print(f"Metrics saved to: {EVAL_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()