import pandas as pd
from pathlib import Path


INPUT_FILE = Path(
    "/opt/airflow/data/processed/unified_vahan_vehicle_market.csv"
)


def main():
    df = pd.read_csv(INPUT_FILE)

    print("===== SQL-STYLE DATA QUALITY REPORT =====")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    print("\n--- Columns ---")
    print(list(df.columns))

    print("\n--- Null Values ---")
    print(df.isnull().sum())

    print("\n--- Duplicate Rows ---")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    print("\n--- Negative Vehicle Counts ---")
    negative_count = (df["Vehicle_Count"] < 0).sum()
    print(f"Negative vehicle counts: {negative_count}")

    print("\n--- Invalid Years ---")
    invalid_years = (
        (df["Year"] < 2016) |
        (df["Year"] > 2026)
    ).sum()
    print(f"Invalid years: {invalid_years}")

    print("\n--- Invalid Months ---")
    valid_months = set(range(1, 13))

    invalid_months = (
        ~df["Month"].isin(valid_months)
    ).sum()

    print(f"Invalid months: {invalid_months}")

    print("\n--- Dataset Types ---")
    print(df["Dataset_Type"].value_counts())

    print("\n--- Missing Dimension Values ---")
    print(df["Dimension_Value"].isnull().sum())

    print("\n--- Missing Source Files ---")
    print(df["Source_File"].isnull().sum())


if __name__ == "__main__":
    main()