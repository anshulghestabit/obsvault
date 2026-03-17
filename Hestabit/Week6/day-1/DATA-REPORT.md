
---

# DATA-Report.md

## 1. Project Overview

This project uses the Ames Housing dataset (`train.csv`) containing 1460 residential property sales records and 81 features.

Objective:
Prepare a cleaned and analysis-ready dataset for regression modeling to predict `SalePrice`.

---

## 2. Initial Dataset Summary

* Rows: 1460
* Columns: 81
* Target Variable: `SalePrice`
* Data Types:

  * 35 numerical (int64)
  * 3 numerical (float64)
  * 43 categorical (string)

Key characteristics:

* Mixture of structural, ordinal, nominal, and continuous variables.
* Multiple columns contain missing values representing either:

  * Structural absence (e.g., no garage)
  * True missing measurements

---

## 3. Missing Value Analysis (Initial)

Columns with highest missing percentage:

| Feature     | Missing % |
| ----------- | --------- |
| PoolQC      | 99.5%     |
| MiscFeature | 96.3%     |
| Alley       | 93.8%     |
| Fence       | 80.7%     |
| MasVnrType  | 59.7%     |
| FireplaceQu | 47.3%     |
| LotFrontage | 17.7%     |

Observation:
Many high-missing columns represent absence of features rather than data errors.
---
## 4. Feature Engineering
### 4.1 Pool Feature

Created:
`HasPool = df['PoolQC'].notnull().astype(int)`

Dropped:

* PoolQC (due to 99% sparsity)
* MiscFeature
* Alley
* Fence

Rationale:
These features were extremely sparse and unlikely to contribute predictive value.

---

## 5. Structured Missing Value Handling

### 5.1 Garage Features

For properties without garages:

* Filled categorical columns with `"None"`
* Set `GarageYrBlt = 0`

Rationale:
Missing garage fields represent structural absence, not measurement failure.

---

### 5.2 Masonry Veneer

* `MasVnrType` → filled with `"None"`
* `MasVnrArea` → filled with `0`

Rationale:
Rows with missing type corresponded to zero veneer area.

---

### 5.3 Basement Features

Verified that rows with missing basement quality had:

* `BsmtFullBath = 0`
* `BsmtHalfBath = 0`

Filled categorical basement fields with `"None"`.

Rationale:
Structural absence of basement.

---

### 5.4 Fireplace Quality

Rows with missing `FireplaceQu` had:

* `Fireplaces = 0`

Filled with `"None"`.

---

### 5.5 LotFrontage (Contextual Imputation)

Imputed using median frontage per `Neighborhood`:

```
df['LotFrontage'] = (
    df.groupby('Neighborhood')['LotFrontage']
      .transform(lambda x: x.fillna(x.median()))
)
```

Fallback:
Global median used if entire group missing.

Rationale:
Lot frontage strongly depends on geographic location.

---

### 5.6 Electrical

One missing value.
Filled using mode:

```
df['Electrical'] = df['Electrical'].fillna(df['Electrical'].mode()[0])
```

---

## 6. Final Dataset

* Final shape: (1460, 78)
* All missing values resolved.
* Saved to:

```
/data/processed/final.csv
```

---

## 7. EDA Outputs Generated

* Correlation matrix (numerical features)
* Feature distribution plots
* Target (`SalePrice`) distribution
* Missing values heatmap

---

## 8. Key Observations

* `OverallQual`, `GrLivArea`, and `TotalBsmtSF` show strong positive correlation with `SalePrice`.
* `SalePrice` is right-skewed.
* Location (`Neighborhood`) is a strong contextual feature.

---

## 9. Engineering Notes

* Structural missing values treated explicitly.
* Context-aware imputation used where appropriate.
* Dataset versioned through processed folder export.
* No target leakage introduced during preprocessing.

---

## 10. Next Steps

* Outlier detection (IQR / Z-score)
* Log transform of `SalePrice`
* Feature scaling
* Train/validation split
* Modeling pipeline construction

---