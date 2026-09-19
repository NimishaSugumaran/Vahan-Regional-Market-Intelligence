import os
import re
from io import StringIO
from pathlib import Path

import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

# Bronze contains the validated State/UT-wise raw CSV files.
RAW_DIR = "/opt/airflow/data/bronze"

OUTPUT_DIR = "/opt/airflow/data/processed"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "unified_vahan_vehicle_market.csv"
)

FAILURE_FILE = os.path.join(
    OUTPUT_DIR,
    "unified_extraction_failed_files.csv"
)


# ============================================================
# DATASET CONFIGURATION
# ============================================================

EXPECTED_DIMENSION_COLUMNS = {
    "Fuel": "Fuel",
    "Manufacturer": "Maker",
    "Vehicle_Category": "Vehicle Category",
    "Vehicle_Class": "Vehicle Class",
    "Vehicle_Type": "Vehicle Type",
    "State": "State",
    "Pollution_Norm": "Norms",
}


SUPPORTED_DATASET_TYPES = set(
    EXPECTED_DIMENSION_COLUMNS.keys()
)


# ============================================================
# DATASET TYPE DETECTION
# ============================================================

def detect_dataset_type(filename):
    """
    Detect dataset type from the Vahan filename.
    """

    filename_lower = os.path.basename(filename).lower()

    # Skip test/sample files.
    if (
        "test" in filename_lower
        or "sample" in filename_lower
    ):
        return "Other"

    if filename_lower.startswith("vahan_fuel_"):
        return "Fuel"

    if filename_lower.startswith("vahan_manufacturer_"):
        return "Manufacturer"

    if filename_lower.startswith("vahan_vehicle_category_"):
        return "Vehicle_Category"

    if filename_lower.startswith("vahan_vehicle_class_"):
        return "Vehicle_Class"

    if filename_lower.startswith("vahan_vehicle_type_"):
        return "Vehicle_Type"

    if filename_lower.startswith("vahan_state_"):
        return "State"

    if filename_lower.startswith("vahan_pollution_norm_"):
        return "Pollution_Norm"

    return "Other"


def is_all_india_file(filename):
    """
    Identify All-India consolidated/yearly files.

    Project scope:
        State/UT-wise monthly reports only.

    Excluded:
        All-India consolidated monthly reports.
        All-India yearly manufacturer reports.
    """

    filename_lower = os.path.basename(filename).lower()

    consolidated_prefixes = (
        "vahan_fuel_monthwise_",
        "vahan_manufacturer_monthwise_",
        "vahan_vehicle_category_monthwise_",
        "vahan_vehicle_class_monthwise_",
        "vahan_vehicle_type_monthwise_",
        "vahan_state_monthwise_",
        "vahan_pollution_norm_monthwise_",
    )

    if filename_lower.startswith(consolidated_prefixes):
        return True

    # Example:
    # vahan_manufacturer_2016_2016.csv
    # vahan_manufacturer_2025_2025.csv
    if re.fullmatch(
        r"vahan_manufacturer_\d{4}_\d{4}\.csv",
        filename_lower
    ):
        return True

    return False


# ============================================================
# HEADER CLEANING
# ============================================================

def clean_header_value(value):
    """
    Clean BOM, quotes, spaces and escaped characters.
    """

    if value is None:
        return ""

    value = str(value)

    value = value.replace("\ufeff", "")
    value = value.replace("\\n", "")
    value = value.replace('"', "")
    value = value.replace("'", "")

    return value.strip()


# ============================================================
# RAW FILE READING
# ============================================================

def read_file_lines(filepath):
    """
    Read raw Vahan CSV safely.
    """

    with open(
        filepath,
        "r",
        encoding="utf-8-sig",
        errors="replace"
    ) as file:

        content = file.read()

    # Convert literal \n into actual line breaks.
    content = content.replace("\\n", "\n")

    return content.splitlines()


def find_header_line(lines, dataset_type):
    """
    Find the actual CSV header row.

    Vahan files generally have a title row first,
    followed by the real header row.
    """

    expected_column = EXPECTED_DIMENSION_COLUMNS.get(dataset_type)

    if expected_column is None:
        raise ValueError(
            f"Unsupported dataset type: {dataset_type}"
        )

    expected_column = clean_header_value(expected_column)

    for index, line in enumerate(lines):

        if not line.strip():
            continue

        clean_line = line.strip()

        clean_line = clean_line.replace("\ufeff", "")
        clean_line = clean_line.replace('"', "")

        first_column = clean_line.split(",")[0]
        first_column = clean_header_value(first_column)

        if first_column.lower() == expected_column.lower():
            return index

    raise ValueError(
        f"Expected column '{expected_column}' not found"
    )


def parse_period_column(column_name):
    """
    Identify month columns such as:

        2016-Jan
        2017-Dec
        2025-Mar
    """

    column_name = clean_header_value(column_name)

    pattern = r"^\d{4}-[A-Za-z]{3}$"

    return bool(re.match(pattern, column_name))


def read_vahan_file(filepath, dataset_type):
    """
    Read a raw Vahan CSV after locating its actual header.
    """

    lines = read_file_lines(filepath)

    header_index = find_header_line(
        lines,
        dataset_type
    )

    csv_content = "\n".join(
        lines[header_index:]
    )

    dataframe = pd.read_csv(
        StringIO(csv_content),
        dtype=str,
        keep_default_na=False
    )

    # Clean column names.
    dataframe.columns = [
        clean_header_value(column)
        for column in dataframe.columns
    ]

    # Clean values.
    for column in dataframe.columns:

        dataframe[column] = (
            dataframe[column]
            .astype(str)
            .str.strip()
            .str.replace("\ufeff", "", regex=False)
            .str.replace('"', "", regex=False)
        )

    return dataframe


# ============================================================
# WIDE TO LONG TRANSFORMATION
# ============================================================

def convert_to_long_format(
    dataframe,
    dataset_type,
    source_file
):
    """
    Convert wide monthly data into long format.

    Example input:

        Maker | 2016-Jan | 2016-Feb | Total

    Example output:

        Dataset_Type
        Dimension_Value
        Period
        Vehicle_Count
    """

    expected_dimension_column = (
        EXPECTED_DIMENSION_COLUMNS[dataset_type]
    )

    # Verify dimension column.
    if expected_dimension_column not in dataframe.columns:

        matching_columns = [
            column
            for column in dataframe.columns
            if clean_header_value(column).lower()
            == expected_dimension_column.lower()
        ]

        if matching_columns:

            dataframe = dataframe.rename(
                columns={
                    matching_columns[0]: expected_dimension_column
                }
            )

        else:

            raise ValueError(
                f"Expected column '{expected_dimension_column}' "
                f"not found. Available columns: "
                f"{list(dataframe.columns)}"
            )

    # Identify monthly columns.
    month_columns = [
        column
        for column in dataframe.columns
        if parse_period_column(column)
    ]

    if not month_columns:
        raise ValueError(
            f"No monthly columns found in {source_file}"
        )

    # Keep dimension + monthly columns only.
    selected_columns = [
        expected_dimension_column
    ] + month_columns

    dataframe = dataframe[selected_columns].copy()

    # Clean dimension values.
    dataframe[expected_dimension_column] = (
        dataframe[expected_dimension_column]
        .astype(str)
        .str.strip()
    )

    # Remove blank dimensions.
    dataframe = dataframe[
        dataframe[expected_dimension_column] != ""
    ]

    # Remove total/summary rows from dimensions.
    dataframe = dataframe[
        ~dataframe[expected_dimension_column]
        .str.lower()
        .isin(
            [
                "total",
                "grand total",
                "all india",
                "all-india",
                "all india total",
            ]
        )
    ]

    # Convert wide to long.
    long_dataframe = dataframe.melt(
        id_vars=[expected_dimension_column],
        value_vars=month_columns,
        var_name="Period",
        value_name="Vehicle_Count"
    )

    # Standardize dimension column.
    long_dataframe = long_dataframe.rename(
        columns={
            expected_dimension_column: "Dimension_Value"
        }
    )

    # Convert counts to numeric.
    long_dataframe["Vehicle_Count"] = pd.to_numeric(
        long_dataframe["Vehicle_Count"],
        errors="coerce"
    ).fillna(0)

    # Replace negative values with zero.
    long_dataframe.loc[
        long_dataframe["Vehicle_Count"] < 0,
        "Vehicle_Count"
    ] = 0

    # Parse YYYY-Mon dates.
    long_dataframe["Period"] = pd.to_datetime(
        long_dataframe["Period"],
        format="%Y-%b",
        errors="coerce"
    )

    # Remove invalid dates.
    long_dataframe = long_dataframe[
        long_dataframe["Period"].notna()
    ]

    # Date attributes.
    long_dataframe["Year"] = (
        long_dataframe["Period"]
        .dt.year
        .astype(int)
    )

    long_dataframe["Month"] = (
        long_dataframe["Period"]
        .dt.month
        .astype(int)
    )

    long_dataframe["Month_Name"] = (
        long_dataframe["Period"]
        .dt.strftime("%B")
    )

    # Metadata.
    long_dataframe["Dataset_Type"] = dataset_type
    long_dataframe["Source_File"] = source_file

    # Final column order.
    long_dataframe = long_dataframe[
        [
            "Dataset_Type",
            "Dimension_Value",
            "Period",
            "Year",
            "Month",
            "Month_Name",
            "Vehicle_Count",
            "Source_File",
        ]
    ]

    return long_dataframe


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_all_vahan_data():
    """
    Extract all supported State/UT-wise Vahan CSV files
    from Bronze recursively.
    """

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    all_dataframes = []
    failed_files = []

    processed_count = 0
    skipped_count = 0
    failed_count = 0

    if not os.path.exists(RAW_DIR):
        raise FileNotFoundError(
            f"Bronze directory not found: {RAW_DIR}"
        )

    # Read CSV files recursively from category/fuel/manufacturer
    # subfolders.
    files = sorted(
        [
            str(file.relative_to(RAW_DIR))
            for file in Path(RAW_DIR).rglob("*.csv")
        ]
    )

    print(
        f"Total CSV files found recursively: {len(files)}"
    )

    for filename in files:

        filepath = os.path.join(
            RAW_DIR,
            filename
        )

        base_filename = os.path.basename(filename)

        dataset_type = detect_dataset_type(
            base_filename
        )

        # Skip All-India consolidated/yearly files.
        if is_all_india_file(base_filename):

            print(
                f"Skipped All-India file: {filename}"
            )

            skipped_count += 1
            continue

        # Skip unsupported/test/sample files.
        if dataset_type == "Other":

            if (
                "test" in base_filename.lower()
                or "sample" in base_filename.lower()
            ):

                print(
                    f"Skipped test/sample file: {filename}"
                )

            else:

                print(
                    f"Skipped unsupported file: {filename}"
                )

            skipped_count += 1
            continue

        try:

            dataframe = read_vahan_file(
                filepath,
                dataset_type
            )

            long_dataframe = convert_to_long_format(
                dataframe,
                dataset_type,
                filename
            )

            if len(long_dataframe) == 0:
                raise ValueError(
                    "No valid rows found after transformation"
                )

            all_dataframes.append(
                long_dataframe
            )

            processed_count += 1

            print(
                f"Processed: {filename} | "
                f"Rows: {len(long_dataframe)}"
            )

        except Exception as error:

            failed_count += 1

            failed_files.append(
                {
                    "File": filename,
                    "Error": str(error)
                }
            )

            print(
                f"Failed: {filename} | "
                f"Error: {error}"
            )

    # Combine processed datasets.
    if all_dataframes:

        unified_dataframe = pd.concat(
            all_dataframes,
            ignore_index=True
        )

    else:

        unified_dataframe = pd.DataFrame(
            columns=[
                "Dataset_Type",
                "Dimension_Value",
                "Period",
                "Year",
                "Month",
                "Month_Name",
                "Vehicle_Count",
                "Source_File",
            ]
        )

    # Remove exact duplicate rows only.
    unified_dataframe = (
        unified_dataframe
        .drop_duplicates()
    )

    # Sort output.
    if not unified_dataframe.empty:

        unified_dataframe = (
            unified_dataframe
            .sort_values(
                by=[
                    "Dataset_Type",
                    "Dimension_Value",
                    "Period",
                    "Source_File",
                ]
            )
            .reset_index(drop=True)
        )

    # Save unified dataset.
    unified_dataframe.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # Save failure report.
    failure_dataframe = pd.DataFrame(
        failed_files,
        columns=[
            "File",
            "Error"
        ]
    )

    failure_dataframe.to_csv(
        FAILURE_FILE,
        index=False
    )

    # Summary.
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    print(
        f"Unified rows: {len(unified_dataframe)}"
    )

    print(
        f"Unified columns: {len(unified_dataframe.columns)}"
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print("\nDataset-wise row counts:")

    if not unified_dataframe.empty:

        print(
            unified_dataframe["Dataset_Type"]
            .value_counts()
        )

    else:

        print("No data available.")

    print(
        f"\nFiles processed: {processed_count}"
    )

    print(
        f"Files skipped: {skipped_count}"
    )

    print(
        f"Files failed: {failed_count}"
    )

    print(
        f"Failure report: {FAILURE_FILE}"
    )

    if failed_count == 0:

        print(
            "\nExtraction completed successfully."
        )

    else:

        print(
            "\nExtraction completed with failures. "
            "Check the failure report."
        )


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    extract_all_vahan_data()