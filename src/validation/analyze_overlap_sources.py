from pathlib import Path
import pandas as pd


PROCESSED_FOLDER = Path("/opt/airflow/data/processed")


def analyze_overlap_sources():

    input_file = (
        PROCESSED_FOLDER
        / "unified_duplicate_records.csv"
    )

    output_file = (
        PROCESSED_FOLDER
        / "unified_overlap_summary.csv"
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

    summary = (
        df.groupby(key_columns)
        .agg(
            Duplicate_Row_Count=(
                "Source_File",
                "count"
            ),
            Unique_Source_Files=(
                "Source_File",
                "nunique"
            ),
            Source_Files=(
                "Source_File",
                lambda x: " | ".join(sorted(set(x)))
            ),
            Vehicle_Counts=(
                "Vehicle_Count",
                lambda x: " | ".join(
                    map(str, sorted(set(x)))
                )
            )
        )
        .reset_index()
    )

    summary = summary.sort_values(
        [
            "Dataset_Type",
            "Unique_Source_Files",
            "Duplicate_Row_Count"
        ],
        ascending=[True, False, False]
    )

    summary.to_csv(
        output_file,
        index=False
    )

    print("========== OVERLAP SOURCE ANALYSIS ==========")
    print(f"Duplicate groups: {len(summary)}")

    print("\nDuplicate groups by dataset:")
    print(
        summary["Dataset_Type"]
        .value_counts()
    )

    print("\nGroups with multiple source files:")
    print(
        summary[
            summary["Unique_Source_Files"] > 1
        ].head(20).to_string(index=False)
    )

    print(
        f"\nOverlap summary saved to: {output_file}"
    )


if __name__ == "__main__":
    analyze_overlap_sources()