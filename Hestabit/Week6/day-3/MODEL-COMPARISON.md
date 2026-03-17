# Model Comparison Report

## Objective
Train and compare multiple regression models for predicting house prices using the Ames Housing dataset.

## Models Trained
- Linear Regression
- Ridge Regression
- Random Forest Regressor
- Gradient Boosting Regressor

## Validation Strategy
- Train-test split: 80/20
- Cross-validation: 5-fold

## Evaluation Metrics
Since Ames Housing is a regression problem, the following metrics were used:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R² Score

## Best Model
The best-performing model selected by the training pipeline was saved automatically as:

`src/models/best_model.pkl`

Evaluation results were saved in:

`src/evaluation/metrics.json`

## Summary
Among the trained models, ensemble-based methods performed better than simple linear models because they captured nonlinear relationships in housing data more effectively. The final selected model can be used for further tuning, interpretation, and deployment in the next stages of the project.