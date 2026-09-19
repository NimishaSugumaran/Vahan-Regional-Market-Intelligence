import pandas as pd
from pathlib import Path
import re

BASE_PATH = Path("/opt/airflow/data/bronze")

MONTH_PATTERN = re.compile(
    r"^\d{4}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$"
)


def validate_folder(folder_name):
    folder_path = BASE_PATH / folder_name
    files = sorted(folder_path.glob("*.csv"))

    valid_files = 0
    invalid_files = []

    print(f"\n===== {folder_name.upper()} =====")
    print(f"Total files: {len(files)}")

    for file in files:
        try:
            df = pd.read_csv(file, encoding="utf-8-sig")

            month_columns = [
                column
                for column in df.columns
                if MONTH_PATTERN.match(str(column))
            ]

            has_total = "Total" in df.columns
            has_rows = len(df) > 0

            if 1 <= len(month_columns) <= 36 and has_total and has_rows:
                valid_files += 1
            else:
                invalid_files.append(
                    {
                        "file": file.name,
                        "rows": len(df),
                        "month_columns": len(month_columns),
                        "has_total": has_total,
                    }
                )

        except Exception as error:
            invalid_files.append(
                {
                    "file": file.name,
                    "error": str(error),
                }
            )

    print(f"Valid files: {valid_files}")
    print(f"Invalid files: {len(invalid_files)}")

    if invalid_files:
        print("\nInvalid file details:")
        for item in invalid_files[:10]:
            print(item)


def main():
    validate_folder("category")
    validate_folder("fuel")


if __name__ == "__main__":
    main()