from pathlib import Path
from datetime import datetime
import csv
import pandas as pd

INPUT_FILE = Path(
    "/opt/airflow/data/processed/silver_vahan_vehicle_market.csv"
)

# Same shared DQ log as the unified-stage validation, so both
# stages' results live in one place, in run order.
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


def validate_silver_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Silver file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

    required_columns = [
        "dataset_type",
        "dimension_value",
        "period",
        "year",
        "month",
        "month_name",
        "vehicle_count",
        "source_file",
        "date"
    ]

    print("===== SILVER VALIDATION =====")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    print(f"Missing required columns: {len(missing_columns)}")

    if missing_columns:
        print("Missing columns:", missing_columns)

        log_validation_result(
            stage="silver_validation",
            status="FAIL",
            rows_checked=len(df),
            critical_error_count=len(missing_columns),
            details=f"Missing columns: {missing_columns}"
        )

        # Previously this just printed and returned, letting the
        # Airflow task report SUCCESS even though validation had
        # actually failed. Raising here makes the task (and DAG)
        # correctly show as failed, matching the unified-stage
        # validation's behaviour.
        raise ValueError(
            "Silver data validation failed: missing required columns."
        )

    null_counts = df[required_columns].isnull().sum()

    print("\nNull Values:")
    print(null_counts)

    duplicate_count = df.duplicated().sum()
    negative_count = (df["vehicle_count"] < 0).sum()

    invalid_year_count = (
        ~df["year"].between(2016, 2026)
    ).sum()

    invalid_month_count = (
        ~df["month"].between(1, 12)
    ).sum()

    invalid_date_count = df["date"].isnull().sum()

    print(f"\nDuplicate Rows: {duplicate_count}")
    print(f"Negative Vehicle Counts: {negative_count}")
    print(f"Invalid Years: {invalid_year_count}")
    print(f"Invalid Months: {invalid_month_count}")
    print(f"Invalid Dates: {invalid_date_count}")

    print("\nDataset Types:")
    print(df["dataset_type"].value_counts())

    print("\nVehicle Count Summary:")
    print(df["vehicle_count"].describe())

    print("\nDate Range:")
    print("Minimum Date:", df["date"].min())
    print("Maximum Date:", df["date"].max())

    # Critical checks - same dimensions as the unified-stage
    # validation, so both stages fail the DAG consistently instead
    # of silver silently letting bad data through.
    critical_errors = []

    if negative_count > 0:
        critical_errors.append(
            f"Negative vehicle counts: {negative_count}"
        )

    if invalid_year_count > 0:
        critical_errors.append(
            f"Invalid years: {invalid_year_count}"
        )

    if invalid_month_count > 0:
        critical_errors.append(
            f"Invalid months: {invalid_month_count}"
        )

    if invalid_date_count > 0:
        critical_errors.append(
            f"Invalid dates: {invalid_date_count}"
        )

    if critical_errors:
        print("\n===== SILVER VALIDATION FAILED =====")

        for error in critical_errors:
            print(f"- {error}")

        log_validation_result(
            stage="silver_validation",
            status="FAIL",
            rows_checked=len(df),
            critical_error_count=len(critical_errors),
            details="; ".join(critical_errors)
        )

        raise ValueError(
            "Silver data validation failed."
        )

    print("\nSilver validation completed successfully.")

    log_validation_result(
        stage="silver_validation",
        status="PASS",
        rows_checked=len(df),
        critical_error_count=0,
        details="All critical checks passed"
    )


if __name__ == "__main__":
    validate_silver_data()