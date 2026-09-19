from pathlib import Path
from datetime import datetime
import csv
import pandas as pd


PROCESSED_FOLDER = Path("/opt/airflow/data/processed")

# Persistent DQ log - every run appends one row here instead of
# results only living in the Airflow task console (which is lost
# once log retention expires).
DQ_LOG_FILE = Path("/opt/airflow/data/logs/dq_validation_log.csv")


def log_validation_result(
    stage,
    status,
    rows_checked,
    critical_error_count,
    details
):
    DQ_LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_exists = DQ_LOG_FILE.exists()

    with open(
        DQ_LOG_FILE,
        mode="a",
        newline="",
        encoding="utf-8"
    ) as log_file:
        writer = csv.writer(log_file)

        if not file_exists:
            writer.writerow(
                [
                    "timestamp",
                    "stage",
                    "status",
                    "rows_checked",
                    "critical_error_count",
                    "details"
                ]
            )

        writer.writerow(
            [
                datetime.now().isoformat(),
                stage,
                status,
                rows_checked,
                critical_error_count,
                details
            ]
        )


def validate_unified_vahan_data():

    input_file = (
        PROCESSED_FOLDER
        / "unified_vahan_vehicle_market_deduplicated.csv"
    )

    if not input_file.exists():
        raise FileNotFoundError(
            f"Deduplicated unified file not found: {input_file}"
        )

    df = pd.read_csv(
        input_file,
        low_memory=False
    )

    print("========== UNIFIED DATA VALIDATION ==========")
    print(f"Input file: {input_file.name}")

    # Required columns
    required_columns = [
        "Dataset_Type",
        "Region",
        "Region_Code",
        "Dimension_Value",
        "Month",
        "Year",
        "Month_Name",
        "Month_Number",
        "Vehicle_Count",
        "Source_File",
        "Title"
    ]

    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    # Basic shape
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # Missing values
    missing_values = df.isnull().sum()

    # Duplicate records
    duplicate_records = df.duplicated().sum()

    # Duplicate business keys
    business_key_columns = [
        "Dataset_Type",
        "Region",
        "Dimension_Value",
        "Month"
    ]

    duplicate_business_keys = (
        df.duplicated(
            subset=business_key_columns
        ).sum()
    )

    # Numeric validation
    numeric_errors = []

    if "Vehicle_Count" in df.columns:
        if not pd.api.types.is_numeric_dtype(
            df["Vehicle_Count"]
        ):
            numeric_errors.append("Vehicle_Count")

    if "Year" in df.columns:
        if not pd.api.types.is_numeric_dtype(
            df["Year"]
        ):
            numeric_errors.append("Year")

    if "Month_Number" in df.columns:
        if not pd.api.types.is_numeric_dtype(
            df["Month_Number"]
        ):
            numeric_errors.append("Month_Number")

    # Negative vehicle counts
    negative_values = (
        df["Vehicle_Count"] < 0
    ).sum()

    # Date validation
    invalid_dates = (
        pd.to_datetime(
            df["Month"],
            errors="coerce"
        ).isnull().sum()
    )

    # Year range validation
    invalid_years = (
        (~df["Year"].between(2016, 2026))
        .sum()
    )

    # Month number validation
    invalid_month_numbers = (
        (~df["Month_Number"].between(1, 12))
        .sum()
    )

    # Dataset type validation
    expected_dataset_types = {
        "Fuel",
        "Manufacturer",
        "Vehicle_Category",
        "State",
        "Pollution_Norm"
    }

    unexpected_dataset_types = sorted(
        set(df["Dataset_Type"].dropna())
        - expected_dataset_types
    )

    # Vehicle count null values
    null_vehicle_counts = (
        df["Vehicle_Count"].isnull().sum()
    )

    # Print validation results
    print("\n----- Column Validation -----")
    print(f"Missing required columns: {missing_columns}")

    print("\n----- Missing Values -----")
    print(
        missing_values[
            missing_values > 0
        ]
    )

    print("\n----- Duplicate Validation -----")
    print(
        f"Duplicate complete records: {duplicate_records}"
    )
    print(
        f"Duplicate business keys: {duplicate_business_keys}"
    )

    print("\n----- Numeric Validation -----")
    print(
        f"Numeric column errors: {numeric_errors}"
    )
    print(
        f"Negative vehicle counts: {negative_values}"
    )
    print(
        f"Null vehicle counts: {null_vehicle_counts}"
    )

    print("\n----- Date Validation -----")
    print(
        f"Invalid dates: {invalid_dates}"
    )
    print(
        f"Invalid years: {invalid_years}"
    )
    print(
        f"Invalid month numbers: {invalid_month_numbers}"
    )

    print("\n----- Dataset Validation -----")
    print(
        f"Unexpected dataset types: "
        f"{unexpected_dataset_types}"
    )

    print("\n----- Dataset-wise Counts -----")
    print(
        df["Dataset_Type"]
        .value_counts()
    )

    # Critical validation failures
    critical_errors = []

    if missing_columns:
        critical_errors.append(
            f"Missing columns: {missing_columns}"
        )

    if numeric_errors:
        critical_errors.append(
            f"Non-numeric columns: {numeric_errors}"
        )

    if negative_values > 0:
        critical_errors.append(
            "Negative vehicle counts found."
        )

    if invalid_dates > 0:
        critical_errors.append(
            "Invalid dates found."
        )

    if invalid_years > 0:
        critical_errors.append(
            "Invalid year values found."
        )

    if invalid_month_numbers > 0:
        critical_errors.append(
            "Invalid month number values found."
        )

    if unexpected_dataset_types:
        critical_errors.append(
            "Unexpected dataset types found."
        )

    if null_vehicle_counts > 0:
        critical_errors.append(
            "Null vehicle counts found."
        )

    if duplicate_business_keys > 0:
        critical_errors.append(
            "Duplicate business keys found."
        )

    # Final validation result
    if critical_errors:
        print("\n========== VALIDATION FAILED ==========")

        for error in critical_errors:
            print(f"- {error}")

        log_validation_result(
            stage="unified_validation",
            status="FAIL",
            rows_checked=len(df),
            critical_error_count=len(critical_errors),
            details="; ".join(critical_errors)
        )

        raise ValueError(
            "Unified Vahan data validation failed."
        )

    print("\n========== VALIDATION PASSED ==========")
    print(
        "All critical data quality checks passed."
    )

    log_validation_result(
        stage="unified_validation",
        status="PASS",
        rows_checked=len(df),
        critical_error_count=0,
        details="All critical checks passed"
    )


if __name__ == "__main__":
    validate_unified_vahan_data()