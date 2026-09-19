import pandas as pd
from pathlib import Path

BASE_PATH = Path("/opt/airflow/data/bronze/manufacturer")


def main():
    files = sorted(BASE_PATH.glob("*.csv"))

    valid_files = 0
    invalid_files = []

    print("===== MANUFACTURER =====")
    print(f"Total files: {len(files)}")

    for file in files:
        try:
            df = pd.read_csv(
                file,
                encoding="utf-8-sig",
                header=None,
                engine="python",
                on_bad_lines="skip"
            )

            if len(df) > 0:
                valid_files += 1
            else:
                invalid_files.append({
                    "file": file.name,
                    "rows": 0
                })

        except Exception as error:
            invalid_files.append({
                "file": file.name,
                "error": str(error)
            })

    print(f"Valid files: {valid_files}")
    print(f"Invalid files: {len(invalid_files)}")

    if invalid_files:
        print("\nInvalid file details:")
        for item in invalid_files[:10]:
            print(item)


if __name__ == "__main__":
    main()