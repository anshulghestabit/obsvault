# Feature Engineering Documentation

## Overview
This module performs structured feature engineering and selection
for the Ames Housing regression problem.

---

## Engineered Features

1. TotalSF
   Basement + 1st floor + 2nd floor

2. TotalBathrooms
   Weighted bathroom count

3. HouseAge
   YrSold - YearBuilt

4. RemodelAge
   YrSold - YearRemodAdd

5. IsRemodeled
   Binary remodel indicator

6. TotalPorchSF
   Sum of all porch areas

7. TotalOutdoorSF
   Deck + Porch area

8. HasGarage
   Binary garage presence

9. HasBasement
   Binary basement presence

10. QualityIndex
    OverallQual × OverallCond

---

## Feature Selection Strategy

1. Remove highly correlated features (> 0.9)
2. Rank features via Mutual Information
3. Apply Recursive Feature Elimination (RandomForest)
4. Take intersection of MI and RFE for robustness

If intersection is empty, fallback to RFE.

---

## Output

Selected feature names are saved to:

src/features/feature_list.json

This ensures reproducibility across training runs.