from pathlib import Path
import pandas as pd


PROCESSED_FOLDER = Path("/opt/airflow/data/processed")


def analyze_duplicates():
    input_file = (
        PROCESSED_FOLDER
        / "unified_vahan_vehicle_market.csv"
    )

    output_file = (
        PROCESSED_FOLDER
        / "unified_duplicate_records.csv"
    )

    df = pd.read_csv(
        input_file,
        low_memory=False
    )

    key_columns = [
        "Dataset_Type",
        "Region",
        "Dimension_Value",
        "Month"
    ]

    duplicates = df[
        df.duplicated(
            subset=key_columns,
            keep=False
        )
    ].copy()

    duplicates = duplicates.sort_values(
        key_columns + ["Source_File"]
    )

    duplicates.to_csv(
        output_file,
        index=False
    )

    print("========== DUPLICATE ANALYSIS ==========")
    print(f"Total duplicate rows: {len(duplicates)}")

    print("\nDuplicates by dataset:")
    print(
        duplicates["Dataset_Type"]
        .value_counts()
    )

    print("\nDuplicates by source file:")
    print(
        duplicates["Source_File"]
        .value_counts()
        .head(20)
    )

    print("\nSample duplicate records:")
    print(
        duplicates[
            key_columns + [
                "Vehicle_Count",
                "Source_File"
            ]
        ].head(20).to_string(index=False)
    )

    print(
        f"\nDuplicate report saved to: {output_file}"
    )


if __name__ == "__main__":
    analyze_duplicates()