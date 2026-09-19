import os
import pandas as pd

INPUT_FILE = "/opt/airflow/data/processed/silver_vahan_vehicle_market.csv"
OUTPUT_FILE = "/opt/airflow/data/processed/silver_vahan_vehicle_market_deduplicated.csv"
LOG_FILE = "/opt/airflow/data/logs/vahan_deduplication_log.csv"

KEY_COLUMNS = [
    "dataset_type",
    "state_code",
    "dimension_value",
    "period",
    "date",
]

def deduplicate_silver_data():
    print("=" * 70)
    print("VAHAN SILVER DEDUPLICATION")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE, low_memory=False)

    print(f"Input rows: {len(df)}")

    duplicate_mask = df.duplicated(
        subset=KEY_COLUMNS,
        keep=False
    )

    duplicate_rows = df[duplicate_mask].copy()

    print(f"Duplicate rows detected: {len(duplicate_rows)}")
    print(
        f"Duplicate business-key groups: "
        f"{duplicate_rows.groupby(KEY_COLUMNS).ngroups}"
    )

    if len(duplicate_rows) > 0:
        value_check = (
            duplicate_rows
            .groupby(KEY_COLUMNS)["vehicle_count"]
            .nunique()
        )

        different_value_groups = int((value_check > 1).sum())

        print(f"Groups with different vehicle counts: {different_value_groups}")

        if different_value_groups > 0:
            raise ValueError(
                "Conflicting vehicle counts found. "
                "Deduplication stopped for data safety."
            )

    # Keep first row because all duplicate business keys
    # have identical vehicle counts.
    deduplicated_df = (
        df
        .drop_duplicates(
            subset=KEY_COLUMNS,
            keep="first"
        )
        .reset_index(drop=True)
    )

    removed_rows = len(df) - len(deduplicated_df)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    deduplicated_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    log_df = pd.DataFrame({
        "input_rows": [len(df)],
        "output_rows": [len(deduplicated_df)],
        "removed_rows": [removed_rows],
        "duplicate_business_key_groups": [
            duplicate_rows.groupby(KEY_COLUMNS).ngroups
            if len(duplicate_rows) > 0 else 0
        ],
        "conflicting_value_groups": [
            different_value_groups
            if len(duplicate_rows) > 0 else 0
        ],
    })

    log_df.to_csv(LOG_FILE, index=False)

    print(f"Output rows: {len(deduplicated_df)}")
    print(f"Removed rows: {removed_rows}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Log file: {LOG_FILE}")
    print("Deduplication completed successfully.")

if __name__ == "__main__":
    deduplicate_silver_data()