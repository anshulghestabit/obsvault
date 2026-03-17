import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "final.csv"
MODELS_DIR = BASE_DIR / "models"
TUNING_DIR = BASE_DIR / "tuning"
EVAL_DIR = BASE_DIR / "evaluation"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
TUNING_DIR.mkdir(parents=True, exist_ok=True)
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


def main():
    X, y = load_data()
    preprocessor = build_preprocessor(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", GradientBoostingRegressor(random_state=42)),
        ]
    )

    param_distributions = {
        "model__n_estimators": [100, 150, 200, 250, 300],
        "model__learning_rate": [0.01, 0.03, 0.05, 0.1],
        "model__max_depth": [2, 3, 4, 5],
        "model__min_samples_split": [2, 5, 10],
        "model__min_samples_leaf": [1, 2, 4],
        "model__subsample": [0.8, 0.9, 1.0],
    }

    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=param_distributions,
        n_iter=20,
        scoring="r2",
        cv=cv,
        verbose=1,
        n_jobs=-1,
        random_state=42,
    )

    search.fit(X_train, y_train)

    best_model = search.best_estimator_
    preds = best_model.predict(X_test)

    test_mae = mean_absolute_error(y_test, preds)
    test_rmse = np.sqrt(mean_squared_error(y_test, preds))
    test_r2 = r2_score(y_test, preds)

    results = {
        "best_params": search.best_params_,
        "best_cv_score_r2": round(search.best_score_, 4),
        "test_metrics": {
            "mae": round(test_mae, 4),
            "rmse": round(test_rmse, 4),
            "r2": round(test_r2, 4),
        },
    }

    with open(TUNING_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=4)

    joblib.dump(best_model, MODELS_DIR / "best_tuned_model.pkl")

    print("Best tuned model saved to:", MODELS_DIR / "best_tuned_model.pkl")
    print("Tuning results saved to:", TUNING_DIR / "results.json")


if __name__ == "__main__":
    main()