import os
import pandas as pd


RAW_PATH = "src/data/raw/house-prices-advanced-regression-techniques/train.csv"
PROCESSED_PATH = "src/data/processed/final.csv"


def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def drop_high_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_to_drop = ['PoolQC', 'MiscFeature', 'Alley', 'Fence']
    return df.drop(columns=cols_to_drop)


def handle_garage(df: pd.DataFrame) -> pd.DataFrame:
    garage_cols = ['GarageType', 'GarageFinish', 'GarageQual', 'GarageCond']
    df[garage_cols] = df[garage_cols].fillna('None')

    df.loc[df['GarageType'] == 'None', 'GarageYrBlt'] = 0
    return df


def handle_masonry(df: pd.DataFrame) -> pd.DataFrame:
    df['MasVnrType'] = df['MasVnrType'].fillna('None')
    df['MasVnrArea'] = df['MasVnrArea'].fillna(0)
    return df


def handle_basement(df: pd.DataFrame) -> pd.DataFrame:
    bsmt_cat_cols = [
        'BsmtQual',
        'BsmtCond',
        'BsmtExposure',
        'BsmtFinType1',
        'BsmtFinType2'
    ]
    df[bsmt_cat_cols] = df[bsmt_cat_cols].fillna('None')
    return df


def handle_fireplace(df: pd.DataFrame) -> pd.DataFrame:
    df['FireplaceQu'] = df['FireplaceQu'].fillna('None')
    return df


def handle_lotfrontage(df: pd.DataFrame) -> pd.DataFrame:
    df['LotFrontage'] = (
        df.groupby('Neighborhood')['LotFrontage']
        .transform(lambda x: x.fillna(x.median()))
    )
    df['LotFrontage'] = df['LotFrontage'].fillna(df['LotFrontage'].median())
    return df


def handle_electrical(df: pd.DataFrame) -> pd.DataFrame:
    df['Electrical'] = df['Electrical'].fillna(df['Electrical'].mode()[0])
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = drop_high_missing_columns(df)
    df = handle_garage(df)
    df = handle_masonry(df)
    df = handle_basement(df)
    df = handle_fireplace(df)
    df = handle_lotfrontage(df)
    df = handle_electrical(df)

    df = df.drop_duplicates()

    return df


def save_data(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)


def main():
    df = load_data(RAW_PATH)
    df = clean_data(df)

    print("Final shape:", df.shape)
    print("Remaining missing values:", df.isnull().sum().sum())

    save_data(df, PROCESSED_PATH)


if __name__ == "__main__":
    main()


'''python src/pipelines/data_pipeline.py
'''