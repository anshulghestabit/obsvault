# Model Interpretation Report

## Objective
The objective of Day 4 was to improve the baseline regression model for the Ames Housing dataset through hyperparameter tuning and add explainability to better understand model predictions.

## Hyperparameter Tuning
The best baseline model from Day 3 was `GradientBoostingRegressor`.
For Day 4, hyperparameter tuning was performed using `RandomizedSearchCV` with 5-fold cross-validation.

The tuning process explored:
- number of estimators
- learning rate
- tree depth
- minimum samples split
- minimum samples leaf
- subsample ratio

The tuning output was saved in:

`src/tuning/results.json`

The tuned model was saved in:

`src/models/best_tuned_model.pkl`

## Explainability Artifacts
The following explainability and error-analysis outputs were generated:

- `src/evaluation/feature_importance.png`
- `src/evaluation/actual_vs_predicted.png`
- `src/evaluation/residual_plot.png`
- `src/evaluation/shap_summary.png`

## Interpretation
Feature importance and SHAP analysis help identify the variables with the strongest influence on house price prediction. In this dataset, features related to living area, overall material quality, basement area, garage capacity, and location tend to contribute strongly to model output.

## Error Analysis
Error analysis was performed using:
- actual vs predicted comparison
- residual plot
- SHAP summary plot

Observations:
- higher-priced houses may show larger prediction error
- rare property combinations are harder for the model to generalize
- tuning improved the robustness of the model compared with the baseline

## Conclusion
Day 4 added both optimization and explainability to the pipeline. The model was tuned successfully, and multiple artifacts were generated to interpret model behavior and analyze prediction errors in a production-style ML workflow.