# Deployment Notes

## Objective
The objective of Day 5 was to deploy the trained Ames Housing regression model as an API and add basic production-style monitoring features.

## API Deployment
The model was deployed using FastAPI with a `POST /predict` endpoint.

Main deployment features:
- model loading with `joblib`
- input schema validation using Pydantic
- request ID tracking using UUID
- versioned model response using environment variable
- prediction logging to CSV

API file:
`src/deployment/api.py`

## Model Loading
The deployed API loads the tuned model from:

`src/models/best_tuned_model.pkl`

## Prediction Logging
Each API request is logged into:

`prediction_logs.csv`

Logged fields include:
- timestamp
- request ID
- model version
- prediction
- raw request payload

## Monitoring
A basic drift checker was added in:

`src/monitoring/drift_checker.py`

This script compares numeric feature means between training data and current batch data and flags large deviations.

## Docker Support
A Dockerfile was created to containerize the API:

`src/deployment/Dockerfile`

## Environment Configuration
The model version can be configured through environment variables.

Example:
`MODEL_VERSION=v1.0`

## Conclusion
Day 5 completes the capstone phase by turning the trained model into a deployable service with logging, validation, versioning, and basic drift monitoring.