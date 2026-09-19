"""
VAHAN MANUFACTURER RECOVERY EXTRACTION
--------------------------------------

Purpose:
    Re-extract ONLY failed Manufacturer reports.

Failed years:
    2019 - 2026

NOT included:
    Manufacturing Year
    Other dimensions

CAPTCHA:
    Manual entry required.

Download fix:
    Detects both:
        1. #downloadBtn
        2. "Download All Records CSV"
"""

import os
import csv
import time
import shutil
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.chrome.options import Options


# ============================================================
# PROJECT PATH
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

# If this script is inside:
# VahanProject\scripts\selenium\
#
# project root = ../../
PROJECT_ROOT = SCRIPT_DIR.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_HTML_DIR = DATA_DIR / "raw_html"
DOWNLOAD_DIR = DATA_DIR / "_downloads"

RAW_DIR.mkdir(parents=True, exist_ok=True)
RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# URL
# ============================================================

URL = (
    "https://analytics.parivahan.gov.in/"
    "analytics/vahanpublicreport?lang=en"
)


# ============================================================
# FAILED JOBS ONLY
# ============================================================

FAILED_YEARS = [
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026,
]


# ============================================================
# REPORT CONFIGURATION
# ============================================================

REPORT_TYPE_VALUE = "0"       # Calendar Year
Y_AXIS_VALUE = "vehicleMakerName"
X_AXIS_VALUE = "monthWise"


# ============================================================
# CHROME SETUP
# ============================================================

def create_driver():

    chrome_options = Options()

    chrome_options.add_argument("--start-maximized")

    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )

    driver = webdriver.Chrome(options=chrome_options)

    return driver


# ============================================================
# WAIT
# ============================================================

def wait_for_page(driver, timeout=30):

    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script(
            "return document.readyState"
        ) == "complete"
    )


# ============================================================
# GET VISIBLE ELEMENT
# ============================================================

def get_visible_select(driver, element_id, timeout=20):

    def find_select(d):

        elements = d.find_elements(
            By.CSS_SELECTOR,
            f"select#{element_id}"
        )

        for element in elements:

            try:

                if element.is_displayed() and element.is_enabled():
                    return element

            except StaleElementReferenceException:
                continue

        return False

    return WebDriverWait(driver, timeout).until(find_select)


# ============================================================
# SELECT BY VALUE - ROBUST VERSION
# ============================================================

def select_by_value(driver, element_id, value, timeout=20):

    print(f"Selecting {element_id} = {value}")

    select_element = get_visible_select(
        driver,
        element_id,
        timeout
    )

    # Print available options
    options = select_element.find_elements(
        By.TAG_NAME,
        "option"
    )

    available = []

    for option in options:

        try:
            available.append(
                (
                    option.get_attribute("value"),
                    option.text.strip()
                )
            )
        except StaleElementReferenceException:
            pass

    print("Available options:", available)

    # Check requested value
    matching = [
        x for x in available
        if x[0] == value
    ]

    if not matching:

        raise Exception(
            f"Option '{value}' not found in #{element_id}"
        )

    # JavaScript selection
    driver.execute_script(
        """
        const select = arguments[0];
        const value = arguments[1];

        select.value = value;

        select.dispatchEvent(
            new Event('input', { bubbles: true })
        );

        select.dispatchEvent(
            new Event('change', { bubbles: true })
        );

        if (window.jQuery) {
            window.jQuery(select)
                .val(value)
                .trigger('input')
                .trigger('change');
        }
        """,
        select_element,
        value,
    )

    # Verify
    def verify(d):

        try:

            elements = d.find_elements(
                By.CSS_SELECTOR,
                f"select#{element_id}"
            )

            for element in elements:

                if (
                    element.is_displayed()
                    and element.is_enabled()
                    and element.get_attribute("value") == value
                ):
                    return True

        except StaleElementReferenceException:
            pass

        return False

    WebDriverWait(driver, timeout).until(verify)

    print(
        f"✓ {element_id} selected -> {value}"
    )


# ============================================================
# WAIT FOR X AXIS OPTION
# ============================================================

def wait_for_x_axis_option(
    driver,
    value,
    timeout=30
):

    print(
        f"Waiting for X-Axis option: {value}"
    )

    def check(d):

        try:

            elements = d.find_elements(
                By.CSS_SELECTOR,
                "select#xAxis"
            )

            for element in elements:

                if not (
                    element.is_displayed()
                    and element.is_enabled()
                ):
                    continue

                options = element.find_elements(
                    By.TAG_NAME,
                    "option"
                )

                for option in options:

                    if option.get_attribute(
                        "value"
                    ) == value:

                        return True

        except StaleElementReferenceException:
            pass

        return False

    WebDriverWait(driver, timeout).until(check)

    print(
        f"✓ X-Axis option available: {value}"
    )


# ============================================================
# SET INPUT VALUE
# ============================================================

def set_input_value(
    driver,
    element_id,
    value,
    timeout=20
):

    element = WebDriverWait(
        driver,
        timeout
    ).until(
        EC.visibility_of_element_located(
            (By.ID, element_id)
        )
    )

    driver.execute_script(
        """
        const element = arguments[0];
        const value = arguments[1];

        element.focus();

        element.value = value;

        element.dispatchEvent(
            new Event('input', { bubbles: true })
        );

        element.dispatchEvent(
            new Event('change', { bubbles: true })
        );

        element.dispatchEvent(
            new Event('blur', { bubbles: true })
        );
        """,
        element,
        str(value),
    )

    WebDriverWait(
        driver,
        timeout
    ).until(
        lambda d:
            d.find_element(
                By.ID,
                element_id
            ).get_attribute("value") == str(value)
    )

    print(
        f"✓ {element_id} = {value}"
    )


# ============================================================
# CONFIGURE REPORT
# ============================================================

def configure_report(
    driver,
    from_year,
    to_year
):

    print("\n" + "=" * 60)
    print("CONFIGURING MANUFACTURER REPORT")
    print("=" * 60)

    # Report Type
    print("Selecting Report Type...")

    select_by_value(
        driver,
        "reportType",
        REPORT_TYPE_VALUE
    )

    # Y Axis
    print("Selecting Y-Axis...")

    select_by_value(
        driver,
        "yAxis",
        Y_AXIS_VALUE
    )

    print("✓ Y-Axis: Manufacturer")

    # Wait for dynamic X axis
    print("Waiting for X-Axis options...")

    wait_for_x_axis_option(
        driver,
        X_AXIS_VALUE
    )

    # X Axis
    print("Selecting X-Axis...")

    select_by_value(
        driver,
        "xAxis",
        X_AXIS_VALUE
    )

    print(
        f"✓ X-Axis: {X_AXIS_VALUE}"
    )

    # Years
    print("Setting year range...")

    set_input_value(
        driver,
        "fromYear",
        from_year
    )

    set_input_value(
        driver,
        "toYear",
        to_year
    )

    # Final verification
    print("\nFINAL CONFIGURATION")
    print("-" * 60)

    report_type = driver.find_element(
        By.ID,
        "reportType"
    ).get_attribute("value")

    y_axis = driver.find_element(
        By.ID,
        "yAxis"
    ).get_attribute("value")

    x_axis = driver.find_element(
        By.ID,
        "xAxis"
    ).get_attribute("value")

    from_value = driver.find_element(
        By.ID,
        "fromYear"
    ).get_attribute("value")

    to_value = driver.find_element(
        By.ID,
        "toYear"
    ).get_attribute("value")

    print("Report Type :", report_type)
    print("Y-Axis      :", y_axis)
    print("X-Axis      :", x_axis)
    print("From Year   :", from_value)
    print("To Year     :", to_value)

    print("-" * 60)

    if report_type != REPORT_TYPE_VALUE:
        raise Exception(
            "Report Type verification failed"
        )

    if y_axis != Y_AXIS_VALUE:
        raise Exception(
            "Y-Axis verification failed"
        )

    if x_axis != X_AXIS_VALUE:
        raise Exception(
            "X-Axis verification failed"
        )

    if from_value != str(from_year):
        raise Exception(
            "From Year verification failed"
        )

    if to_value != str(to_year):
        raise Exception(
            "To Year verification failed"
        )

    print(
        "✓ ALL CONFIGURATION VALUES VERIFIED"
    )


# ============================================================
# CAPTCHA CHECKPOINT
# ============================================================

def captcha_checkpoint(
    driver,
    from_year,
    to_year
):

    print("\n")
    print("=" * 70)
    print("MANUAL CAPTCHA CHECKPOINT")
    print("=" * 70)

    print(
        f"Dimension : Manufacturer"
    )

    print(
        f"Years     : {from_year} - {to_year}"
    )

    print()
    print(
        "Enter CAPTCHA manually in Chrome."
    )

    print(
        "Do not close Chrome."
    )

    print("=" * 70)

    input(
        "After entering CAPTCHA, press ENTER..."
    )


# ============================================================
# APPLY BUTTON
# ============================================================

def click_apply(driver):

    print("\nApplying report...")

    # Primary ID
    elements = driver.find_elements(
        By.ID,
        "applyTrigger"
    )

    for element in elements:

        try:

            if (
                element.is_displayed()
                and element.is_enabled()
            ):

                driver.execute_script(
                    "arguments[0].click();",
                    element
                )

                print("Apply clicked.")

                return

        except Exception:
            continue

    # Fallback
    xpaths = [
        "//button[contains(normalize-space(.),'Apply')]",
        "//input[@type='button' and contains(@value,'Apply')]",
        "//input[@type='submit' and contains(@value,'Apply')]",
    ]

    for xpath in xpaths:

        elements = driver.find_elements(
            By.XPATH,
            xpath
        )

        for element in elements:

            try:

                if (
                    element.is_displayed()
                    and element.is_enabled()
                ):

                    driver.execute_script(
                        "arguments[0].click();",
                        element
                    )

                    print(
                        "Apply clicked using fallback."
                    )

                    return

            except Exception:
                continue

    raise Exception(
        "Apply button not found."
    )


# ============================================================
# WAIT FOR TABLE
# ============================================================

def wait_for_table(driver, timeout=120):

    print(
        "Waiting for report table..."
    )

    def find_table(d):

        tables = d.find_elements(
            By.TAG_NAME,
            "table"
        )

        for table in tables:

            try:

                if not table.is_displayed():
                    continue

                rows = table.find_elements(
                    By.CSS_SELECTOR,
                    "tr"
                )

                if len(rows) >= 2:
                    return table

            except StaleElementReferenceException:
                continue

        return False

    table = WebDriverWait(
        driver,
        timeout
    ).until(find_table)

    print(
        "Report table detected."
    )

    return table


# ============================================================
# SAVE HTML
# ============================================================

def save_html(
    driver,
    year
):

    filename = (
        f"vahan_manufacturer_{year}_{year}.html"
    )

    path = RAW_HTML_DIR / filename

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            driver.page_source
        )

    print(
        f"HTML saved: {path}"
    )

    return path


# ============================================================
# CLEAR DOWNLOAD FOLDER
# ============================================================

def clear_download_folder():

    for item in DOWNLOAD_DIR.iterdir():

        try:

            if item.is_file():
                item.unlink()

            elif item.is_dir():
                shutil.rmtree(item)

        except Exception:
            pass


# ============================================================
# FIND DOWNLOAD BUTTON
# ============================================================

def find_download_button(
    driver,
    timeout=30
):

    print(
        "Searching for Download All Records CSV..."
    )

    def find_button(d):

        # ----------------------------------------------------
        # 1. Original known ID
        # ----------------------------------------------------

        try:

            elements = d.find_elements(
                By.ID,
                "downloadBtn"
            )

            for element in elements:

                if (
                    element.is_displayed()
                    and element.is_enabled()
                ):

                    return element

        except Exception:
            pass

        # ----------------------------------------------------
        # 2. Exact / partial visible text
        # ----------------------------------------------------

        xpaths = [

            "//button[contains(normalize-space(.),"
            "'Download All Records CSV')]",

            "//a[contains(normalize-space(.),"
            "'Download All Records CSV')]",

            "//*[contains(normalize-space(.),"
            "'Download All Records CSV')]",

            "//button[contains(normalize-space(.),"
            "'Download CSV')]",

            "//a[contains(normalize-space(.),"
            "'Download CSV')]",

        ]

        for xpath in xpaths:

            try:

                elements = d.find_elements(
                    By.XPATH,
                    xpath
                )

                for element in elements:

                    if (
                        element.is_displayed()
                        and element.is_enabled()
                    ):

                        return element

            except Exception:
                continue

        return False

    try:

        button = WebDriverWait(
            driver,
            timeout
        ).until(find_button)

        print(
            "✓ Download button found."
        )

        return button

    except TimeoutException:

        # Debug information
        print(
            "\nDownload button could not be found."
        )

        print(
            "\nVisible buttons/links on page:"
        )

        elements = driver.find_elements(
            By.XPATH,
            "//button | //a"
        )

        for element in elements:

            try:

                if element.is_displayed():

                    text = element.text.strip()

                    if text:
                        print(
                            "  ->",
                            repr(text)
                        )

            except Exception:
                pass

        raise Exception(
            "Download button not found."
        )


# ============================================================
# CLICK DOWNLOAD
# ============================================================

def click_download(
    driver,
    button
):

    print(
        "Clicking download button..."
    )

    try:

        driver.execute_script(
            """
            arguments[0].scrollIntoView({
                block: 'center'
            });
            """,
            button
        )

        time.sleep(1)

        driver.execute_script(
            "arguments[0].click();",
            button
        )

        print(
            "✓ Download button clicked."
        )

    except Exception as first_error:

        print(
            "Normal JS click failed:"
        )
        print(first_error)

        try:

            button.click()

            print(
                "✓ Fallback click successful."
            )

        except Exception as second_error:

            raise Exception(
                f"Download click failed: "
                f"{second_error}"
            )


# ============================================================
# WAIT FOR CSV
# ============================================================

def wait_for_csv(
    timeout=120
):

    print(
        "Waiting for CSV download..."
    )

    end_time = time.time() + timeout

    while time.time() < end_time:

        files = list(
            DOWNLOAD_DIR.glob("*")
        )

        # Ignore Chrome temporary downloads
        csv_files = [
            f
            for f in files
            if f.is_file()
            and f.suffix.lower() == ".csv"
        ]

        crdownload = [
            f
            for f in files
            if f.name.endswith(".crdownload")
        ]

        if csv_files and not crdownload:

            # Pick newest CSV
            latest = max(
                csv_files,
                key=lambda x: x.stat().st_mtime
            )

            # Make sure file size is stable
            size1 = latest.stat().st_size

            time.sleep(1)

            size2 = latest.stat().st_size

            if size1 == size2 and size2 > 0:

                print(
                    f"✓ CSV downloaded: {latest.name}"
                )

                return latest

        time.sleep(1)

    raise Exception(
        "CSV download timeout."
    )


# ============================================================
# MOVE CSV TO FINAL LOCATION
# ============================================================

def save_csv(
    downloaded_file,
    year
):

    filename = (
        f"vahan_manufacturer_{year}_{year}.csv"
    )

    destination = RAW_DIR / filename

    if destination.exists():

        destination.unlink()

    shutil.move(
        str(downloaded_file),
        str(destination)
    )

    print(
        f"CSV saved: {destination}"
    )

    return destination


# ============================================================
# CHECK EXISTING OUTPUT
# ============================================================

def output_exists(year):

    filename = (
        f"vahan_manufacturer_{year}_{year}.csv"
    )

    path = RAW_DIR / filename

    return path.exists()


# ============================================================
# SINGLE YEAR EXTRACTION
# ============================================================

def extract_year(
    driver,
    year
):

    print("\n")
    print("#" * 75)

    print(
        f"MANUFACTURER RECOVERY"
    )

    print(
        f"YEAR : {year}"
    )

    print("#" * 75)

    # --------------------------------------------------------
    # Skip if already downloaded
    # --------------------------------------------------------

    if output_exists(year):

        print(
            f"✓ Already exists. Skipping {year}."
        )

        return "SKIPPED"

    # --------------------------------------------------------
    # Configure
    # --------------------------------------------------------

    configure_report(
        driver,
        year,
        year
    )

    # --------------------------------------------------------
    # CAPTCHA
    # --------------------------------------------------------

    captcha_checkpoint(
        driver,
        year,
        year
    )

    # --------------------------------------------------------
    # Apply
    # --------------------------------------------------------

    click_apply(driver)

    # --------------------------------------------------------
    # Table
    # --------------------------------------------------------

    wait_for_table(
        driver,
        timeout=120
    )

    # --------------------------------------------------------
    # Save HTML evidence
    # --------------------------------------------------------

    save_html(
        driver,
        year
    )

    # --------------------------------------------------------
    # Clear previous download
    # --------------------------------------------------------

    clear_download_folder()

    # --------------------------------------------------------
    # IMPORTANT:
    # Wait for actual download button
    # --------------------------------------------------------

    button = find_download_button(
        driver,
        timeout=60
    )

    # --------------------------------------------------------
    # Click
    # --------------------------------------------------------

    click_download(
        driver,
        button
    )

    # --------------------------------------------------------
    # Wait CSV
    # --------------------------------------------------------

    csv_file = wait_for_csv(
        timeout=120
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_csv(
        csv_file,
        year
    )

    print(
        f"✓ MANUFACTURER {year} SUCCESS"
    )

    return "SUCCESS"


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 75)
    print("VAHAN MANUFACTURER RECOVERY EXTRACTION")
    print("=" * 75)

    print(
        "Only failed Manufacturer years will be processed."
    )

    print(
        "Years:",
        FAILED_YEARS
    )

    print(
        "Manufacturing Year will NOT be processed."
    )

    print("=" * 75)

    driver = create_driver()

    results = []

    try:

        # ----------------------------------------------------
        # Open portal
        # ----------------------------------------------------

        print("\nOpening VAHAN portal...")

        driver.get(URL)

        wait_for_page(
            driver,
            timeout=60
        )

        print(
            "✓ Portal loaded."
        )

        input(
            "\nPress ENTER when page is ready..."
        )

        # ----------------------------------------------------
        # Process only failed years
        # ----------------------------------------------------

        total = len(FAILED_YEARS)

        for index, year in enumerate(
            FAILED_YEARS,
            start=1
        ):

            print("\n")
            print(
                f"PROGRESS: {index}/{total}"
            )

            try:

                status = extract_year(
                    driver,
                    year
                )

                results.append(
                    (year, status)
                )

            except Exception as error:

                print("\n")
                print("!" * 75)

                print(
                    f"FAILED: Manufacturer {year}"
                )

                print(
                    "ERROR:",
                    error
                )

                print("!" * 75)

                results.append(
                    (year, "FAILED")
                )

                # Continue to next year
                continue

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print("\n\n")
        print("=" * 75)
        print("RECOVERY EXTRACTION SUMMARY")
        print("=" * 75)

        success = 0
        skipped = 0
        failed = 0

        for year, status in results:

            print(
                f"{year} -> {status}"
            )

            if status == "SUCCESS":
                success += 1

            elif status == "SKIPPED":
                skipped += 1

            elif status == "FAILED":
                failed += 1

        print("-" * 75)

        print(
            f"Success : {success}"
        )

        print(
            f"Skipped : {skipped}"
        )

        print(
            f"Failed  : {failed}"
        )

        print("-" * 75)

        print(
            "\nOutput folder:"
        )

        print(
            RAW_DIR
        )

        print(
            "\nRecovery completed."
        )

    finally:

        print(
            "\nChrome session kept open."
        )

        print(
            "Review the final results before closing Chrome."
        )

        # Uncomment this only when you want
        # the browser to close automatically.
        #
        # driver.quit()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()