from pathlib import Path
import pandas as pd


PROCESSED_FOLDER = Path("/opt/airflow/data/processed")
LOADED_FOLDER = Path("/opt/airflow/data/loaded")


def load_vahan_data():

    input_file = (
        PROCESSED_FOLDER
        / "silver_vahan_vehicle_market_deduplicated.csv"
    )

    output_file = (
        LOADED_FOLDER
        / "vahan_vehicle_market_loaded.csv"
    )

    if not input_file.exists():
        raise FileNotFoundError(
            f"Deduplicated Silver file not found: {input_file}"
        )

    LOADED_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    df = pd.read_csv(
        input_file,
        encoding="utf-8-sig",
        low_memory=False
    )

    print("=" * 70)
    print("VAHAN DATA LOADING")
    print("=" * 70)

    print(f"Input file: {input_file.name}")
    print(f"Input rows: {len(df)}")

    required_columns = [
        "dataset_type",
        "dimension_value",
        "period",
        "year",
        "month",
        "month_name",
        "vehicle_count",
        "source_file",
        "state_code",
        "state",
        "date"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Remove aggregate rows if present
    aggregate_values = {
        "TOTAL",
        "GRAND TOTAL"
    }

    before_filter = len(df)

    df = df[
        ~df["dimension_value"]
        .astype(str)
        .str.upper()
        .isin(aggregate_values)
    ].copy()

    removed_aggregates = before_filter - len(df)

    # Final duplicate check
    business_key_columns = [
        "dataset_type",
        "state_code",
        "dimension_value",
        "period",
        "date"
    ]

    duplicate_mask = df.duplicated(
        subset=business_key_columns,
        keep=False
    )

    duplicate_count = int(duplicate_mask.sum())

    duplicate_groups = int(
        df.loc[duplicate_mask]
        .groupby(
            business_key_columns,
            dropna=False
        )
        .ngroups
    )

    if duplicate_count > 0:
        print("\nDuplicate business key sample:")

        print(
            df.loc[
                duplicate_mask,
                business_key_columns
                + ["source_file", "vehicle_count"]
            ]
            .head(20)
            .to_string(index=False)
        )

        raise ValueError(
            f"Duplicate business keys found: "
            f"{duplicate_count} rows across "
            f"{duplicate_groups} groups"
        )

    # Sort data
    df = df.sort_values(
        [
            "dataset_type",
            "state_code",
            "dimension_value",
            "date"
        ]
    ).reset_index(drop=True)

    # Save loaded output
    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nAggregate rows removed: {removed_aggregates}")
    print(f"Output rows: {len(df)}")
    print(f"Output columns: {len(df.columns)}")
    print(f"Duplicate business keys: {duplicate_count}")
    print(f"Loaded file: {output_file}")

    print("\n----- Dataset-wise Counts -----")
    print(df["dataset_type"].value_counts())

    print("\n----- State-wise Counts -----")
    print(df["state"].value_counts().head(10))

    print("\n" + "=" * 70)
    print("LOADING COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    load_vahan_data()