from pathlib import Path
from datetime import datetime
import csv
import uuid
import os

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "best_tuned_model.pkl"
LOG_PATH = Path(__file__).resolve().parents[2] / "prediction_logs.csv"

MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0")


app = FastAPI(title="Ames Housing Price Prediction API")


class HouseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    MSSubClass: int
    MSZoning: str
    LotFrontage: float | None = None
    LotArea: int
    Street: str
    Alley: str | None = None
    LotShape: str
    LandContour: str
    Utilities: str
    LotConfig: str
    LandSlope: str
    Neighborhood: str
    Condition1: str
    Condition2: str
    BldgType: str
    HouseStyle: str
    OverallQual: int
    OverallCond: int
    YearBuilt: int
    YearRemodAdd: int
    RoofStyle: str
    RoofMatl: str
    Exterior1st: str
    Exterior2nd: str
    MasVnrType: str | None = None
    MasVnrArea: float | None = None
    ExterQual: str
    ExterCond: str
    Foundation: str
    BsmtQual: str | None = None
    BsmtCond: str | None = None
    BsmtExposure: str | None = None
    BsmtFinType1: str | None = None
    BsmtFinSF1: float
    BsmtFinType2: str | None = None
    BsmtFinSF2: float
    BsmtUnfSF: float
    TotalBsmtSF: float
    Heating: str
    HeatingQC: str
    CentralAir: str
    Electrical: str
    FirstFlrSF: float
    SecondFlrSF: float
    LowQualFinSF: float
    GrLivArea: float
    BsmtFullBath: float
    BsmtHalfBath: float
    FullBath: int
    HalfBath: int
    BedroomAbvGr: int
    KitchenAbvGr: int
    KitchenQual: str
    TotRmsAbvGrd: int
    Functional: str
    Fireplaces: int
    FireplaceQu: str | None = None
    GarageType: str | None = None
    GarageYrBlt: float | None = None
    GarageFinish: str | None = None
    GarageCars: float
    GarageArea: float
    GarageQual: str | None = None
    GarageCond: str | None = None
    PavedDrive: str
    WoodDeckSF: float
    OpenPorchSF: float
    EnclosedPorch: float
    ThreeSsnPorch: float
    ScreenPorch: float
    PoolArea: float
    PoolQC: str | None = None
    Fence: str | None = None
    MiscFeature: str | None = None
    MiscVal: float
    MoSold: int
    YrSold: int
    SaleType: str
    SaleCondition: str


def normalize_input(data: dict) -> dict:
    rename_map = {
        "FirstFlrSF": "1stFlrSF",
        "SecondFlrSF": "2ndFlrSF",
        "ThreeSsnPorch": "3SsnPorch",
        "BedroomAbvGr": "BedroomAbvGr",
        "KitchenAbvGr": "KitchenAbvGr",
    }
    normalized = {}
    for key, value in data.items():
        normalized[rename_map.get(key, key)] = value
    return normalized


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


model = load_model()


def log_prediction(request_id: str, payload: dict, prediction: float):
    file_exists = LOG_PATH.exists()

    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                ["timestamp", "request_id", "model_version", "prediction", "payload"]
            )
        writer.writerow(
            [
                datetime.datetime.utcnow().isoformat(),
                request_id,
                MODEL_VERSION,
                round(prediction, 4),
                str(payload),
            ]
        )


@app.get("/")
def root():
    return {
        "message": "Ames Housing Prediction API is running",
        "model_version": MODEL_VERSION,
    }


@app.post("/predict")
def predict(input_data: HouseInput):
    try:
        request_id = str(uuid.uuid4())
        payload = normalize_input(input_data.model_dump())
        df = pd.DataFrame([payload])

        prediction = float(model.predict(df)[0])

        log_prediction(request_id, payload, prediction)

        return {
            "request_id": request_id,
            "model_version": MODEL_VERSION,
            "predicted_sale_price": round(prediction, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")