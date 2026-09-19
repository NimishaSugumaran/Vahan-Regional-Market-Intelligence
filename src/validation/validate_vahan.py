from pathlib import Path
import pandas as pd


PROCESSED_FOLDER = Path("/opt/airflow/data/processed")


def validate_vahan_data():
    input_file = (
        PROCESSED_FOLDER
        / "vahan_fuel_tn_monthwise_2016_2018_extracted.csv"
    )

    if not input_file.exists():
        raise FileNotFoundError(f"Extracted file not found: {input_file}")

    df = pd.read_csv(input_file)

    # Required columns
    required_columns = ["Fuel", "Total", "State", "Source_File"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    # Duplicate fuel categories
    duplicate_fuels = df["Fuel"].duplicated().sum()

    # Missing values
    missing_values = df.isnull().sum().sum()

    # Numeric monthly columns
    month_columns = [
        col for col in df.columns
        if "-" in col and col[:4].isdigit()
    ]

    numeric_errors = []

    for col in month_columns + ["Total"]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            numeric_errors.append(col)

    # Negative values
    negative_values = (
        df[month_columns + ["Total"]] < 0
    ).sum().sum()

    # Summary
    print("Validation completed.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Monthly columns: {len(month_columns)}")
    print(f"Duplicate fuel rows: {duplicate_fuels}")
    print(f"Missing values: {missing_values}")
    print(f"Numeric column errors: {numeric_errors}")
    print(f"Negative values: {negative_values}")

    # Fail pipeline if critical issues exist
    if missing_columns:
        raise ValueError("Validation failed due to missing columns.")

    if numeric_errors:
        raise ValueError(
            f"Validation failed due to non-numeric columns: {numeric_errors}"
        )

    if negative_values > 0:
        raise ValueError("Validation failed: negative vehicle counts found.")

    print("Validation status: PASSED")


if __name__ == "__main__":
    validate_vahan_data()