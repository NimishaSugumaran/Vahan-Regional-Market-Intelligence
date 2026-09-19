from pathlib import Path
import pandas as pd
from io import StringIO


RAW_FOLDER = Path("/opt/airflow/data/raw")
PROCESSED_FOLDER = Path("/opt/airflow/data/processed")


def read_vahan_csv(file_path):
    """
    Reads Vahan CSV files that contain a title line
    followed by the actual CSV header.
    """

    text = file_path.read_text(encoding="utf-8")

    # Convert literal \n characters into actual line breaks
    text = text.replace("\\n", "\n")

    lines = text.splitlines()

    # Locate the actual CSV header
    header_index = next(
        i for i, line in enumerate(lines)
        if line.startswith("Fuel,")
    )

    csv_text = "\n".join(lines[header_index:])

    return pd.read_csv(StringIO(csv_text))


def extract_vahan_data():
    PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

    input_file = RAW_FOLDER / "vahan_fuel_tn_monthwise_2016_2018.csv"
    output_file = PROCESSED_FOLDER / "vahan_fuel_tn_monthwise_2016_2018_extracted.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    df = read_vahan_csv(input_file)

    # Add source metadata
    df["State"] = "Tamil Nadu"
    df["Source_File"] = input_file.name

    df.to_csv(output_file, index=False)

    print("Extraction completed successfully.")
    print(f"Input rows: {len(df)}")
    print(f"Input columns: {len(df.columns)}")
    print(f"Output file: {output_file}")


if __name__ == "__main__":
    extract_vahan_data()