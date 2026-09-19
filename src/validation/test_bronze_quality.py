import pandas as pd
from pathlib import Path
import re


BASE_PATH = Path(__file__).resolve().parents[2] / "data" / "bronze"


MONTH_PATTERN = re.compile(
    r"^\d{4}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$"
)


def get_csv_files(folder_name):
    return sorted((BASE_PATH / folder_name).glob("*.csv"))


def test_category_file_count():
    assert len(get_csv_files("category")) == 144


def test_fuel_file_count():
    assert len(get_csv_files("fuel")) == 144


def test_manufacturer_file_count():
    assert len(get_csv_files("manufacturer")) == 396


def test_category_files_have_required_structure():
    for file in get_csv_files("category"):
        df = pd.read_csv(file, encoding="utf-8-sig")

        month_columns = [
            column
            for column in df.columns
            if MONTH_PATTERN.match(str(column))
        ]

        assert len(month_columns) >= 1
        assert "Total" in df.columns
        assert len(df) > 0


def test_fuel_files_have_required_structure():
    for file in get_csv_files("fuel"):
        df = pd.read_csv(file, encoding="utf-8-sig")

        month_columns = [
            column
            for column in df.columns
            if MONTH_PATTERN.match(str(column))
        ]

        assert len(month_columns) >= 1
        assert "Total" in df.columns
        assert len(df) > 0


def test_manufacturer_files_are_readable():
    for file in get_csv_files("manufacturer"):
        df = pd.read_csv(
            file,
            encoding="utf-8-sig",
            header=None,
            engine="python",
            on_bad_lines="skip"
        )

        assert len(df) > 0