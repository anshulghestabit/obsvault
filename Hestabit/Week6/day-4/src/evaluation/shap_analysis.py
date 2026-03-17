from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "final.csv"
MODEL_PATH = BASE_DIR / "models" / "best_tuned_model.pkl"
EVAL_DIR = BASE_DIR / "evaluation"

EVAL_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    df = pd.read_csv(DATA_PATH)

    if "Id" in df.columns:
        df = df.drop(columns=["Id"])

    X = df.drop(columns=["SalePrice"])
    y = df["SalePrice"]
    return X, y


def save_feature_importance(model, feature_names):
    regressor = model.named_steps["model"]

    if not hasattr(regressor, "feature_importances_"):
        print("Model does not support feature importance.")
        return

    importances = regressor.feature_importances_
    top_n = min(20, len(importances))
    indices = np.argsort(importances)[-top_n:]

    plt.figure(figsize=(10, 6))
    plt.barh(range(top_n), importances[indices])
    plt.yticks(range(top_n), [feature_names[i] for i in indices])
    plt.xlabel("Importance")
    plt.title("Top Feature Importances")
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "feature_importance.png")
    plt.close()

    print("Saved:", EVAL_DIR / "feature_importance.png")


def save_prediction_plots(y_test, preds):
    # Actual vs Predicted
    plt.figure(figsize=(8, 6))
    plt.scatter(y_test, preds, alpha=0.6)
    plt.xlabel("Actual SalePrice")
    plt.ylabel("Predicted SalePrice")
    plt.title("Actual vs Predicted SalePrice")
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "actual_vs_predicted.png")
    plt.close()

    print("Saved:", EVAL_DIR / "actual_vs_predicted.png")

    # Residual plot
    residuals = y_test - preds
    plt.figure(figsize=(8, 6))
    plt.scatter(preds, residuals, alpha=0.6)
    plt.axhline(y=0, linestyle="--")
    plt.xlabel("Predicted SalePrice")
    plt.ylabel("Residuals")
    plt.title("Residual Plot")
    plt.tight_layout()
    plt.savefig(EVAL_DIR / "residual_plot.png")
    plt.close()

    print("Saved:", EVAL_DIR / "residual_plot.png")


def try_shap(model, X_train):
    try:
        import shap
    except ImportError:
        print("SHAP not installed. Skipping SHAP summary plot.")
        return

    try:
        preprocessor = model.named_steps["preprocessor"]
        regressor = model.named_steps["model"]

        X_train_transformed = preprocessor.transform(X_train)

        feature_names = preprocessor.get_feature_names_out()

        # sample for speed
        sample_size = min(200, X_train_transformed.shape[0])

        if hasattr(X_train_transformed, "toarray"):
            X_sample = X_train_transformed[:sample_size].toarray()
        else:
            X_sample = X_train_transformed[:sample_size]

        explainer = shap.Explainer(regressor, X_sample)
        shap_values = explainer(X_sample)

        plt.figure()
        shap.summary_plot(
            shap_values,
            X_sample,
            feature_names=feature_names,
            show=False
        )
        plt.tight_layout()
        plt.savefig(EVAL_DIR / "shap_summary.png", bbox_inches="tight")
        plt.close()

        print("Saved:", EVAL_DIR / "shap_summary.png")

    except Exception as e:
        print("SHAP analysis skipped due to error:", str(e))


def main():
    X, y = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = joblib.load(MODEL_PATH)
    preds = model.predict(X_test)

    preprocessor = model.named_steps["preprocessor"]
    feature_names = preprocessor.get_feature_names_out()

    save_feature_importance(model, feature_names)
    save_prediction_plots(y_test, preds)
    try_shap(model, X_train)


if __name__ == "__main__":
    main()