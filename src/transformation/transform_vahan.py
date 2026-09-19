from pathlib import Path
import re
import pandas as pd


PROCESSED_FOLDER = Path("/opt/airflow/data/processed")

INPUT_FILE = PROCESSED_FOLDER / "unified_vahan_vehicle_market.csv"
OUTPUT_FILE = PROCESSED_FOLDER / "silver_vahan_vehicle_market.csv"
ERROR_LOG_FILE = PROCESSED_FOLDER / "silver_transformation_errors.csv"


STATE_MAPPING = {
    "an": "Andaman and Nicobar Islands",
    "ap": "Andhra Pradesh",
    "ar": "Arunachal Pradesh",
    "as": "Assam",
    "br": "Bihar",
    "ch": "Chandigarh",
    "cg": "Chhattisgarh",
    "ct": "Chhattisgarh",
    "dd": "Daman and Diu",
    "dl": "Delhi",
    "dn": "Dadra and Nagar Haveli",
    "ga": "Goa",
    "gj": "Gujarat",
    "hp": "Himachal Pradesh",
    "hr": "Haryana",
    "jk": "Jammu and Kashmir",
    "jh": "Jharkhand",
    "ka": "Karnataka",
    "kl": "Kerala",
    "la": "Ladakh",
    "ld": "Lakshadweep",
    "mh": "Maharashtra",
    "ml": "Meghalaya",
    "mn": "Manipur",
    "mp": "Madhya Pradesh",
    "mz": "Mizoram",
    "nl": "Nagaland",
    "od": "Odisha",
    "or": "Odisha",
    "pb": "Punjab",
    "py": "Puducherry",
    "rj": "Rajasthan",
    "sk": "Sikkim",
    "tn": "Tamil Nadu",
    "tr": "Tripura",
    "ts": "Telangana",
    "tg": "Telangana",
    "uk": "Uttarakhand",
    "up": "Uttar Pradesh",
    "wb": "West Bengal",
}


def extract_state_code(source_file):
    """
    Extract the two-letter state code from a state-wise VAHAN filename.

    Examples:
    fuel/vahan_fuel_tn_monthwise_2016_2018.csv
    -> tn

    manufacturer/vahan_manufacturer_cg_monthwise_2016_2018.csv
    -> cg
    """

    filename = Path(str(source_file)).name.lower()

    patterns = [
        r"vahan_fuel_([a-z]{2})_",
        r"vahan_manufacturer_([a-z]{2})_",
        r"vahan_vehicle_category_([a-z]{2})_",
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)

        if match:
            return match.group(1)

    return pd.NA


def transform_vahan_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig"
    )

    required_columns = [
        "Dataset_Type",
        "Dimension_Value",
        "Period",
        "Year",
        "Month",
        "Month_Name",
        "Vehicle_Count",
        "Source_File",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    silver_df = df.rename(
        columns={
            "Dataset_Type": "dataset_type",
            "Dimension_Value": "dimension_value",
            "Period": "period",
            "Year": "year",
            "Month": "month",
            "Month_Name": "month_name",
            "Vehicle_Count": "vehicle_count",
            "Source_File": "source_file",
        }
    ).copy()

    # Clean text columns
    text_columns = [
        "dataset_type",
        "dimension_value",
        "period",
        "month_name",
        "source_file",
    ]

    for column in text_columns:
        silver_df[column] = (
            silver_df[column]
            .astype("string")
            .str.strip()
        )

    # Extract state code from source filename
    silver_df["state_code"] = (
        silver_df["source_file"]
        .apply(extract_state_code)
        .astype("string")
        .str.lower()
    )

    # Map state code to state name
    silver_df["state"] = (
        silver_df["state_code"]
        .map(STATE_MAPPING)
        .astype("string")
    )

    # Convert numeric columns
    silver_df["year"] = pd.to_numeric(
        silver_df["year"],
        errors="coerce"
    )

    silver_df["month"] = pd.to_numeric(
        silver_df["month"],
        errors="coerce"
    )

    silver_df["vehicle_count"] = pd.to_numeric(
        silver_df["vehicle_count"],
        errors="coerce"
    )

    # Create proper date column
    silver_df["date"] = pd.to_datetime(
        silver_df["year"].astype("Int64").astype(str)
        + "-"
        + silver_df["month"].astype("Int64").astype(str)
        + "-01",
        errors="coerce"
    )

    # Validation masks
    invalid_year = (
        silver_df["year"].isna()
        | ~silver_df["year"].between(2016, 2026)
    )

    invalid_month = (
        silver_df["month"].isna()
        | ~silver_df["month"].between(1, 12)
    )

    invalid_vehicle_count = (
        silver_df["vehicle_count"].isna()
        | (silver_df["vehicle_count"] < 0)
    )

    invalid_dimension = (
        silver_df["dimension_value"].isna()
        | (silver_df["dimension_value"] == "")
    )

    invalid_dataset_type = (
        silver_df["dataset_type"].isna()
        | (silver_df["dataset_type"] == "")
    )

    invalid_state = (
        silver_df["state_code"].isna()
        | silver_df["state"].isna()
    )

    invalid_mask = (
        invalid_year
        | invalid_month
        | invalid_vehicle_count
        | invalid_dimension
        | invalid_dataset_type
        | invalid_state
    )

    # Create error log
    errors = []

    if invalid_mask.any():
        error_df = silver_df.loc[invalid_mask].copy()

        error_df["error_reason"] = ""

        error_df.loc[
            invalid_year,
            "error_reason"
        ] += "Invalid year; "

        error_df.loc[
            invalid_month,
            "error_reason"
        ] += "Invalid month; "

        error_df.loc[
            invalid_vehicle_count,
            "error_reason"
        ] += "Invalid vehicle count; "

        error_df.loc[
            invalid_dimension,
            "error_reason"
        ] += "Missing dimension value; "

        error_df.loc[
            invalid_dataset_type,
            "error_reason"
        ] += "Missing dataset type; "

        error_df.loc[
            invalid_state,
            "error_reason"
        ] += "Missing or invalid state code; "

        errors.append(error_df)

    # Keep valid rows
    silver_df = silver_df.loc[~invalid_mask].copy()

    # Remove only exact duplicates
    before_duplicates = len(silver_df)

    silver_df = silver_df.drop_duplicates().copy()

    removed_duplicates = (
        before_duplicates - len(silver_df)
    )

    # Sort Silver data
    silver_df = silver_df.sort_values(
        [
            "dataset_type",
            "state",
            "dimension_value",
            "year",
            "month",
        ]
    ).reset_index(drop=True)

    # Save Silver output
    silver_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # Save transformation errors
    if errors:
        error_log = pd.concat(
            errors,
            ignore_index=True
        )

        error_log.to_csv(
            ERROR_LOG_FILE,
            index=False,
            encoding="utf-8-sig"
        )
    else:
        if ERROR_LOG_FILE.exists():
            ERROR_LOG_FILE.unlink()

    # Summary
    print("===== SILVER TRANSFORMATION =====")
    print(f"Input rows: {len(df)}")
    print(f"Output rows: {len(silver_df)}")
    print(f"Output columns: {len(silver_df.columns)}")
    print(f"Removed exact duplicates: {removed_duplicates}")
    print(f"Rejected rows: {int(invalid_mask.sum())}")
    print(f"Output file: {OUTPUT_FILE}")

    print("\nState-wise row counts:")
    print(silver_df["state"].value_counts().head(10))

    if errors:
        print(f"\nError log: {ERROR_LOG_FILE}")
    else:
        print("Error log: No rejected rows")


if __name__ == "__main__":
    transform_vahan_data()