# ============================================================
# VAHAN BULK SELENIUM EXTRACTION
# Historical Data: 2016-2026
# CAPTCHA: MANUAL ONLY
# ============================================================

import os
import csv
import time
import shutil
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    WebDriverException,
)


# ============================================================
# CONFIGURATION
# ============================================================

URL = "https://analytics.parivahan.gov.in/analytics/vahanpublicreport?lang=en"

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
HTML_DIR = os.path.join(PROJECT_ROOT, "data", "raw_html")
LOG_DIR = os.path.join(PROJECT_ROOT, "data", "logs")

DOWNLOAD_DIR = os.path.join(RAW_DIR, "_downloads")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ============================================================
# YEAR PLAN
# ============================================================

# All normal dimensions support 3-year ranges.
YEAR_CHUNKS = [
    (2016, 2018),
    (2019, 2021),
    (2022, 2024),
    (2025, 2026),
]


# ============================================================
# REPORT JOBS
# ============================================================

# year_mode:
#   chunk3 = 3-year extraction
#   single = one year at a time
#
# x:
#   monthWise = Month Wise
#   Total Consolidated = Manufacturing Year requirement
#
# RTO is intentionally excluded because it was not available
# as the current Y-axis option we verified.

REPORT_JOBS = [

    {
        "name": "vehicle_category",
        "y": "vehicleCategoryDescription",
        "x": "monthWise",
        "label": "Vehicle Category",
        "year_mode": "chunk3",
    },

    {
        "name": "vehicle_class",
        "y": "vehicleClass",
        "x": "monthWise",
        "label": "Vehicle Class",
        "year_mode": "chunk3",
    },

    {
        "name": "vehicle_type",
        "y": "vehicleType",
        "x": "monthWise",
        "label": "Vehicle Type",
        "year_mode": "chunk3",
    },

    {
        "name": "pollution_norm",
        "y": "vehiclePollutionNorm",
        "x": "monthWise",
        "label": "Pollution Norm",
        "year_mode": "chunk3",
    },

    {
        "name": "fuel",
        "y": "vehicleFuel",
        "x": "monthWise",
        "label": "Fuel",
        "year_mode": "chunk3",
    },

    {
        "name": "state",
        "y": "stateCode",
        "x": "monthWise",
        "label": "State",
        "year_mode": "chunk3",
    },

    {
        "name": "manufacturer",
        "y": "vehicleMakerName",
        "x": "monthWise",
        "label": "Manufacturer",
        "year_mode": "single",
    },

    {
        "name": "manufacturing_year",
        "y": "vehicleManufecturingYear",
        "x": "Total Consolidated",
        "label": "Manufacturing Year",
        "year_mode": "chunk3",
    },
]


REPORT_TYPE_VALUE = "0"       # Calendar Year


# ============================================================
# CHROME SETUP
# ============================================================

options = webdriver.ChromeOptions()

options.add_experimental_option(
    "prefs",
    {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
)

options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 30)


# ============================================================
# LOG FILE
# ============================================================

LOG_FILE = os.path.join(
    LOG_DIR,
    "vahan_extraction_log.csv"
)


def initialize_log():

    if not os.path.exists(LOG_FILE):

        with open(
            LOG_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "timestamp",
                "job",
                "dimension",
                "from_year",
                "to_year",
                "status",
                "csv_file",
                "html_file",
                "message"
            ])


def write_log(
    job,
    dimension,
    from_year,
    to_year,
    status,
    csv_file="",
    html_file="",
    message=""
):

    with open(
        LOG_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            job,
            dimension,
            from_year,
            to_year,
            status,
            csv_file,
            html_file,
            message
        ])


initialize_log()


# ============================================================
# YEAR RANGE HELPER
# ============================================================

def get_year_ranges(job):

    if job["year_mode"] == "single":

        return [
            (year, year)
            for year in range(2016, 2027)
        ]

    return YEAR_CHUNKS


# ============================================================
# OUTPUT PATHS
# ============================================================

def get_csv_path(
    job,
    from_year,
    to_year
):

    if job["x"] == "monthWise":

        x_name = "monthwise"

    else:

        x_name = "total_consolidated"

    return os.path.join(
        RAW_DIR,
        f"vahan_{job['name']}_"
        f"{x_name}_"
        f"{from_year}_{to_year}.csv"
    )


def get_html_path(
    job,
    from_year,
    to_year
):

    return os.path.join(
        HTML_DIR,
        f"vahan_{job['name']}_"
        f"{from_year}_{to_year}.html"
    )


# ============================================================
# CHECK EXISTING FILE
# ============================================================

def output_already_exists(
    job,
    from_year,
    to_year
):

    path = get_csv_path(
        job,
        from_year,
        to_year
    )

    return os.path.exists(path)


# ============================================================
# SELECT DROPDOWN
# ============================================================

def select_by_value(element_id, value):

    print(
        f"Selecting {element_id} = {value}"
    )

    # --------------------------------------------------------
    # Find the visible + enabled SELECT element.
    # The portal can dynamically rebuild dropdowns.
    # --------------------------------------------------------

    end_time = time.time() + 20
    element = None

    while time.time() < end_time:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                f"select#{element_id}"
            )

            for candidate in elements:

                try:

                    if (
                        candidate.is_displayed()
                        and candidate.is_enabled()
                    ):
                        element = candidate
                        break

                except StaleElementReferenceException:
                    continue

            if element is not None:
                break

        except Exception:
            pass

        time.sleep(0.5)

    if element is None:

        raise TimeoutException(
            f"Visible select not found: #{element_id}"
        )

    # --------------------------------------------------------
    # Read available options.
    # --------------------------------------------------------

    options = element.find_elements(
        By.TAG_NAME,
        "option"
    )

    available = [
        (
            option.get_attribute("value"),
            option.text.strip()
        )
        for option in options
    ]

    print(
        "Available options:",
        available
    )

    # --------------------------------------------------------
    # Match by VALUE first, then visible TEXT.
    # --------------------------------------------------------

    matched_value = None

    for option in options:

        option_value = option.get_attribute("value")

        if option_value == str(value):

            matched_value = option_value
            break

    if matched_value is None:

        for option in options:

            option_text = option.text.strip()

            if option_text.lower() == str(value).lower():

                matched_value = option.get_attribute("value")
                break

    if matched_value is None:

        raise NoSuchElementException(
            f"Option '{value}' not found in #{element_id}. "
            f"Available={available}"
        )

    # --------------------------------------------------------
    # Set the value through JavaScript and fire both native
    # and jQuery change events.
    # This is only normal form interaction; CAPTCHA remains
    # manual and is never solved or bypassed.
    # --------------------------------------------------------

    driver.execute_script(
        """
        const select = arguments[0];
        const value = arguments[1];

        select.value = value;

        select.dispatchEvent(
            new Event('input', {
                bubbles: true
            })
        );

        select.dispatchEvent(
            new Event('change', {
                bubbles: true
            })
        );

        if (window.jQuery) {

            window.jQuery(select)
                .val(value)
                .trigger('input')
                .trigger('change');

        }
        """,
        element,
        matched_value
    )

    # --------------------------------------------------------
    # Verify the selection actually stuck.
    # --------------------------------------------------------

    def selected_correctly(_):

        try:

            current = element.get_attribute(
                "value"
            )

            return str(current) == str(matched_value)

        except (
            StaleElementReferenceException,
            WebDriverException
        ):

            return False

    try:

        WebDriverWait(
            driver,
            10
        ).until(selected_correctly)

    except TimeoutException:

        # Re-find the visible element once because the portal
        # may rebuild the SELECT after the change event.

        fresh_elements = driver.find_elements(
            By.CSS_SELECTOR,
            f"select#{element_id}"
        )

        fresh = None

        for candidate in fresh_elements:

            try:

                if (
                    candidate.is_displayed()
                    and candidate.is_enabled()
                ):
                    fresh = candidate
                    break

            except StaleElementReferenceException:
                continue

        if fresh is None:

            raise TimeoutException(
                f"#{element_id} disappeared after selection."
            )

        current = fresh.get_attribute(
            "value"
        )

        if str(current) != str(matched_value):

            raise TimeoutException(
                f"Selection failed for #{element_id}: "
                f"requested={matched_value}, "
                f"actual={current}"
            )

        element = fresh

    print(
        f"✓ {element_id} selected -> {matched_value}"
    )

    time.sleep(0.8)


def wait_for_x_axis_option(value, timeout=20):

    print(
        f"Waiting for X-Axis option: {value}"
    )

    end_time = time.time() + timeout

    while time.time() < end_time:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                "select#xAxis"
            )

            for element in elements:

                try:

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

                        if (
                            option.get_attribute("value")
                            == str(value)
                        ):
                            print(
                                f"✓ X-Axis option available: {value}"
                            )
                            return True

                except StaleElementReferenceException:
                    continue

        except WebDriverException:
            pass

        time.sleep(0.5)

    return False


# ============================================================
# SET INPUT# ============================================================
# SET INPUT
# ============================================================

def set_input_value(
    element_id,
    value
):

    element = wait.until(
        EC.presence_of_element_located(
            (By.ID, element_id)
        )
    )

    driver.execute_script(
        """
        arguments[0].removeAttribute('readonly');

        arguments[0].value = arguments[1];

        arguments[0].dispatchEvent(
            new Event('input', {bubbles:true})
        );

        arguments[0].dispatchEvent(
            new Event('change', {bubbles:true})
        );

        arguments[0].dispatchEvent(
            new Event('blur', {bubbles:true})
        );
        """,
        element,
        str(value)
    )


# ============================================================
# GET INPUT VALUE
# ============================================================

def get_input_value(
    element_id
):

    try:

        element = driver.find_element(
            By.ID,
            element_id
        )

        return element.get_attribute(
            "value"
        ) or ""

    except Exception:

        return ""


# ============================================================
# CLEAR TEMP DOWNLOADS
# ============================================================

def clear_download_folder():

    for filename in os.listdir(
        DOWNLOAD_DIR
    ):

        path = os.path.join(
            DOWNLOAD_DIR,
            filename
        )

        try:

            if os.path.isfile(path):

                os.remove(path)

            elif os.path.isdir(path):

                shutil.rmtree(path)

        except Exception:

            pass


# ============================================================
# WAIT FOR TABLE
# ============================================================

def wait_for_table(
    timeout=60
):

    end_time = (
        time.time() + timeout
    )

    while time.time() < end_time:

        try:

            tables = driver.find_elements(
                By.TAG_NAME,
                "table"
            )

            for table in tables:

                rows = table.find_elements(
                    By.TAG_NAME,
                    "tr"
                )

                if len(rows) >= 2:

                    return True

        except (
            StaleElementReferenceException,
            WebDriverException
        ):

            pass

        time.sleep(2)

    return False


# ============================================================
# WAIT FOR DOWNLOAD BUTTON
# ============================================================

def wait_for_download_button(
    timeout=30
):

    end_time = (
        time.time() + timeout
    )

    while time.time() < end_time:

        try:

            button = driver.find_element(
                By.ID,
                "downloadBtn"
            )

            if button.is_displayed():

                return True

        except (
            NoSuchElementException,
            StaleElementReferenceException
        ):

            pass

        time.sleep(1)

    return False


# ============================================================
# WAIT FOR CSV
# ============================================================

def wait_for_csv(
    timeout=45
):

    end_time = (
        time.time() + timeout
    )

    while time.time() < end_time:

        files = os.listdir(
            DOWNLOAD_DIR
        )

        csv_files = [
            f
            for f in files
            if f.lower().endswith(".csv")
        ]

        if csv_files:

            csv_files.sort(
                key=lambda f:
                os.path.getmtime(
                    os.path.join(
                        DOWNLOAD_DIR,
                        f
                    )
                ),
                reverse=True
            )

            return os.path.join(
                DOWNLOAD_DIR,
                csv_files[0]
            )

        time.sleep(1)

    return None


# ============================================================
# SAVE HTML
# ============================================================

def save_html(
    path
):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            driver.page_source
        )

    return path


# ============================================================
# CLICK BUTTON
# ============================================================

def click_button(
    button_id
):

    for attempt in range(3):

        try:

            button = wait.until(
                EC.presence_of_element_located(
                    (By.ID, button_id)
                )
            )

            driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block:'center'
                });
                """,
                button
            )

            time.sleep(0.5)

            button = driver.find_element(
                By.ID,
                button_id
            )

            driver.execute_script(
                "arguments[0].click();",
                button
            )

            return True

        except (
            StaleElementReferenceException,
            WebDriverException,
            TimeoutException
        ):

            time.sleep(1)

    return False


# ============================================================
# VISIBLE PORTAL MESSAGES
# ============================================================

def get_visible_messages():

    messages = []

    selectors = [
        ".alert",
        ".alert-danger",
        ".alert-warning",
        ".text-danger",
        ".error",
        ".warning"
    ]

    for selector in selectors:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            for element in elements:

                if element.is_displayed():

                    text = element.text.strip()

                    if text:

                        messages.append(
                            text
                        )

        except Exception:

            pass

    return list(
        dict.fromkeys(messages)
    )


# ============================================================
# CAPTCHA CHECKPOINT
# ============================================================

def captcha_checkpoint(
    job_label,
    from_year,
    to_year
):

    try:

        captcha = driver.find_element(
            By.ID,
            "externalCaptcha"
        )

        if not captcha.is_displayed():

            return

    except Exception:

        return


    print()
    print("=" * 70)
    print("MANUAL CAPTCHA CHECKPOINT")
    print("=" * 70)

    print(
        f"Dimension : {job_label}"
    )

    print(
        f"Years     : "
        f"{from_year} - {to_year}"
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

    # We only verify that something was entered.
    # CAPTCHA solving/bypass is NOT attempted.

    value = get_input_value(
        "externalCaptcha"
    )

    if not value.strip():

        print()
        print(
            "CAPTCHA field is empty."
        )

        input(
            "Enter CAPTCHA and press ENTER..."
        )


# ============================================================
# CONFIGURE REPORT
# ============================================================

def configure_report(
    job,
    from_year,
    to_year
):

    print()
    print("=" * 60)
    print("CONFIGURING REPORT")
    print("=" * 60)

    # --------------------------------------------------------
    # REPORT TYPE
    # --------------------------------------------------------

    print(
        "Selecting Report Type..."
    )

    select_by_value(
        "reportType",
        REPORT_TYPE_VALUE
    )

    # --------------------------------------------------------
    # Y AXIS
    # --------------------------------------------------------

    print(
        "Selecting Y-Axis..."
    )

    select_by_value(
        "yAxis",
        job["y"]
    )

    print(
        "✓ Y-Axis:",
        job["label"]
    )

    # --------------------------------------------------------
    # X AXIS
    #
    # X-Axis options are rebuilt dynamically after Y-Axis.
    # Do not use a fixed sleep here.
    # --------------------------------------------------------

    print(
        "Waiting for X-Axis options..."
    )

    if not wait_for_x_axis_option(
        job["x"],
        timeout=20
    ):

        try:

            x_elements = driver.find_elements(
                By.CSS_SELECTOR,
                "select#xAxis"
            )

            print()
            print(
                "Current X-Axis options:"
            )

            for x_element in x_elements:

                try:

                    if not x_element.is_displayed():
                        continue

                    for option in x_element.find_elements(
                        By.TAG_NAME,
                        "option"
                    ):

                        print(
                            "  VALUE =",
                            option.get_attribute("value"),
                            "| TEXT =",
                            option.text.strip()
                        )

                except Exception:
                    pass

        except Exception:
            pass

        raise TimeoutException(
            f"X-Axis option '{job['x']}' "
            f"did not appear after Y-Axis selection."
        )

    print(
        "Selecting X-Axis..."
    )

    select_by_value(
        "xAxis",
        job["x"]
    )

    print(
        "✓ X-Axis:",
        job["x"]
    )

    # --------------------------------------------------------
    # YEAR RANGE
    # --------------------------------------------------------

    print(
        "Setting year range..."
    )

    set_input_value(
        "fromYear",
        from_year
    )

    set_input_value(
        "toYear",
        to_year
    )

    time.sleep(1)

    # --------------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------------

    print()
    print(
        "FINAL CONFIGURATION"
    )
    print(
        "-" * 60
    )

    report_type = driver.find_element(
        By.ID,
        "reportType"
    ).get_attribute(
        "value"
    )

    y_axis = driver.find_element(
        By.ID,
        "yAxis"
    ).get_attribute(
        "value"
    )

    x_axis = driver.find_element(
        By.ID,
        "xAxis"
    ).get_attribute(
        "value"
    )

    from_value = get_input_value(
        "fromYear"
    )

    to_value = get_input_value(
        "toYear"
    )

    print(
        "Report Type :",
        report_type
    )

    print(
        "Y-Axis      :",
        y_axis
    )

    print(
        "X-Axis      :",
        x_axis
    )

    print(
        "From Year   :",
        from_value
    )

    print(
        "To Year     :",
        to_value
    )

    print(
        "-" * 60
    )

    # --------------------------------------------------------
    # HARD VERIFICATION
    # --------------------------------------------------------

    if str(report_type) != str(
        REPORT_TYPE_VALUE
    ):

        raise Exception(
            f"Report Type mismatch: "
            f"{report_type} != {REPORT_TYPE_VALUE}"
        )

    if str(y_axis) != str(
        job["y"]
    ):

        raise Exception(
            f"Y-Axis mismatch: "
            f"{y_axis} != {job['y']}"
        )

    if str(x_axis) != str(
        job["x"]
    ):

        raise Exception(
            f"X-Axis mismatch: "
            f"{x_axis} != {job['x']}"
        )

    if str(from_value) != str(
        from_year
    ):

        raise Exception(
            f"From Year mismatch: "
            f"{from_value} != {from_year}"
        )

    if str(to_value) != str(
        to_year
    ):

        raise Exception(
            f"To Year mismatch: "
            f"{to_value} != {to_year}"
        )

    print(
        "✓ ALL CONFIGURATION VALUES VERIFIED"
    )

    print(
        "=" * 60
    )


# ============================================================
# SINGLE EXTRACTION
# ============================================================
# SINGLE EXTRACTION
# ============================================================

def extract_report(
    job,
    from_year,
    to_year
):

    job_name = job["name"]
    label = job["label"]

    print()
    print("=" * 75)

    print(
        f"EXTRACTION: {label}"
    )

    print(
        f"YEAR RANGE: "
        f"{from_year} - {to_year}"
    )

    print(
        f"X-AXIS: {job['x']}"
    )

    print("=" * 75)


    # --------------------------------------------------------
    # SKIP EXISTING SUCCESSFUL FILE
    # --------------------------------------------------------

    if output_already_exists(
        job,
        from_year,
        to_year
    ):

        existing = get_csv_path(
            job,
            from_year,
            to_year
        )

        print()
        print(
            "SKIPPED - CSV already exists:"
        )

        print(existing)

        write_log(
            job_name,
            label,
            from_year,
            to_year,
            "SKIPPED",
            existing,
            "",
            "CSV already exists"
        )

        return "SKIPPED"


    try:

        # ----------------------------------------------------
        # KEEP SAME BROWSER SESSION
        # ----------------------------------------------------

        wait.until(
            EC.presence_of_element_located(
                (By.ID, "yAxis")
            )
        )


        # ----------------------------------------------------
        # CONFIGURE
        # ----------------------------------------------------

        configure_report(
            job,
            from_year,
            to_year
        )


        # ----------------------------------------------------
        # CAPTCHA
        # ----------------------------------------------------

        captcha_checkpoint(
            label,
            from_year,
            to_year
        )


        # ----------------------------------------------------
        # APPLY
        # ----------------------------------------------------

        print()
        print(
            "Applying report..."
        )

        if not click_button(
            "applyTrigger"
        ):

            raise Exception(
                "Apply button could not be clicked."
            )

        print(
            "Apply clicked."
        )


        # ----------------------------------------------------
        # WAIT TABLE
        # ----------------------------------------------------

        print(
            "Waiting for report table..."
        )

        if not wait_for_table(60):

            messages = (
                get_visible_messages()
            )

            if messages:

                raise Exception(
                    "Portal message: "
                    + " | ".join(messages)
                )

            raise Exception(
                "Report table not detected."
            )


        print(
            "Report table detected."
        )


        # ----------------------------------------------------
        # SAVE HTML EVIDENCE
        # ----------------------------------------------------

        html_path = get_html_path(
            job,
            from_year,
            to_year
        )

        save_html(
            html_path
        )

        print(
            "HTML saved:",
            html_path
        )


        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        if not wait_for_download_button(
            30
        ):

            raise Exception(
                "Download button not found."
            )


        clear_download_folder()

        time.sleep(1)


        if not click_button(
            "downloadBtn"
        ):

            raise Exception(
                "Download button click failed."
            )


        print(
            "Download clicked."
        )


        # ----------------------------------------------------
        # WAIT CSV
        # ----------------------------------------------------

        downloaded_file = wait_for_csv(
            45
        )

        if not downloaded_file:

            raise Exception(
                "CSV download not detected."
            )


        print(
            "CSV downloaded:",
            downloaded_file
        )


        # ----------------------------------------------------
        # FINAL FILE
        # ----------------------------------------------------

        final_path = get_csv_path(
            job,
            from_year,
            to_year
        )


        if os.path.exists(
            final_path
        ):

            os.remove(
                final_path
            )


        shutil.move(
            downloaded_file,
            final_path
        )


        print()
        print(
            "CSV saved:",
            final_path
        )


        # ----------------------------------------------------
        # SUCCESS LOG
        # ----------------------------------------------------

        write_log(
            job_name,
            label,
            from_year,
            to_year,
            "SUCCESS",
            final_path,
            html_path,
            "Extraction completed successfully"
        )


        print()
        print(
            "SUCCESS"
        )

        return "SUCCESS"


    except Exception as e:

        print()
        print(
            "FAILED:",
            str(e)
        )


        # ----------------------------------------------------
        # FAILURE HTML
        # ----------------------------------------------------

        failure_html = os.path.join(
            HTML_DIR,
            f"FAILED_{job_name}_"
            f"{from_year}_{to_year}.html"
        )

        try:

            save_html(
                failure_html
            )

        except Exception:

            failure_html = ""


        write_log(
            job_name,
            label,
            from_year,
            to_year,
            "FAILED",
            "",
            failure_html,
            str(e)
        )


        return "FAILED"


# ============================================================
# MAIN
# ============================================================

try:

    print()
    print("=" * 75)
    print(
        "VAHAN BULK SELENIUM EXTRACTION"
    )
    print(
        "PERIOD: 2016-2026"
    )
    print(
        "CAPTCHA: MANUAL"
    )
    print("=" * 75)


    driver.get(URL)


    wait.until(
        EC.presence_of_element_located(
            (By.ID, "yAxis")
        )
    )


    print()
    print(
        "VAHAN portal opened."
    )

    print()
    print(
        "If CAPTCHA is visible, enter it manually."
    )

    print(
        "Keep Chrome open."
    )

    input(
        "Press ENTER when page is ready..."
    )


    # --------------------------------------------------------
    # TOTAL JOB COUNT
    # --------------------------------------------------------

    total = sum(
        len(get_year_ranges(job))
        for job in REPORT_JOBS
    )


    print()
    print(
        "Total planned reports:",
        total
    )

    print()


    completed = 0
    skipped = 0
    failed = 0
    current = 0


    # --------------------------------------------------------
    # BULK LOOP
    # --------------------------------------------------------

    for job in REPORT_JOBS:

        for from_year, to_year in get_year_ranges(
            job
        ):

            current += 1

            print()
            print()
            print("#" * 75)

            print(
                f"JOB {current}/{total}"
            )

            print(
                f"Dimension : "
                f"{job['label']}"
            )

            print(
                f"Years     : "
                f"{from_year}-{to_year}"
            )

            print(
                f"Y-Axis    : "
                f"{job['y']}"
            )

            print(
                f"X-Axis    : "
                f"{job['x']}"
            )

            print("#" * 75)


            result = extract_report(
                job,
                from_year,
                to_year
            )


            if result == "SUCCESS":

                completed += 1

            elif result == "SKIPPED":

                skipped += 1

            else:

                failed += 1


            print()
            print(
                f"Progress: "
                f"{current}/{total}"
            )

            print(
                f"Success: {completed} | "
                f"Skipped: {skipped} | "
                f"Failed: {failed}"
            )


            time.sleep(2)


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 75)
    print(
        "BULK EXTRACTION COMPLETED"
    )
    print("=" * 75)

    print(
        "Total planned :",
        total
    )

    print(
        "Successful    :",
        completed
    )

    print(
        "Skipped       :",
        skipped
    )

    print(
        "Failed        :",
        failed
    )

    print()
    print(
        "RAW CSV folder:"
    )

    print(
        RAW_DIR
    )

    print()
    print(
        "HTML evidence folder:"
    )

    print(
        HTML_DIR
    )

    print()
    print(
        "Extraction log:"
    )

    print(
        LOG_FILE
    )

    print()
    print("=" * 75)

    input(
        "Press ENTER to close Chrome..."
    )


finally:

    driver.quit()