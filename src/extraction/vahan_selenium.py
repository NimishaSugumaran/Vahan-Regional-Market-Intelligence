# ============================================================
# VAHAN STATE-WISE MASTER EXTRACTION - OPTIMIZED
# ============================================================
# Project:
#   Vahan Regional Vehicle Market Intelligence Platform
#
# Purpose:
#   State-wise:
#       1. Vehicle Category
#       2. Fuel
#       3. Manufacturer
#
# Period:
#   2016 - 2026
#
# CAPTCHA:
#   MANUAL ONLY
#
# TOTAL REPORTS:
#   Category     = 36 × 4  = 144
#   Fuel         = 36 × 4  = 144
#   Manufacturer = 36 × 11 = 396
#   TOTAL                   = 684
#
# OPTIMIZATION:
#   - Page is NOT reloaded for every report.
#   - State is selected ONCE per state.
#   - All reports for a state are processed together.
#   - Existing CSV files are skipped.
#   - CAPTCHA remains manual.
#
# IMPORTANT:
#   No CAPTCHA bypass.
#   No synthetic data.
# ============================================================

from pathlib import Path
import csv
import re
import shutil
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException,
)


# ============================================================
# PROJECT PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
RAW_HTML_DIR = DATA_DIR / "raw_html"
DOWNLOAD_DIR = DATA_DIR / "_downloads"
LOG_DIR = DATA_DIR / "logs"

LOG_FILE = LOG_DIR / "vahan_statewise_master_log.csv"


# ============================================================
# VAHAN URL
# ============================================================

URL = (
    "https://analytics.parivahan.gov.in/"
    "analytics/vahanpublicreport?lang=en"
)


# ============================================================
# GENERAL SETTINGS
# ============================================================

REPORT_TYPE_VALUE = "0"

WAIT_TIMEOUT = 45
LONG_WAIT = 60

# Optimized waits
YEAR_STABLE_SECONDS = 1.5
CONFIG_SETTLE_SECONDS = 1.5

DOWNLOAD_TIMEOUT = 90
PAGE_LOAD_TIMEOUT = 120


# ============================================================
# YEAR CHUNKS
# ============================================================

YEAR_CHUNKS = [
    (2016, 2018),
    (2019, 2021),
    (2022, 2024),
    (2025, 2026),
]


# ============================================================
# ALL STATES
# ============================================================

STATES = [
    ("AN", "Andaman and Nicobar Islands"),
    ("AP", "Andhra Pradesh"),
    ("AR", "Arunachal Pradesh"),
    ("AS", "Assam"),
    ("BR", "Bihar"),
    ("CH", "Chandigarh"),
    ("CG", "Chhattisgarh"),
    ("DL", "Delhi"),
    ("GA", "Goa"),
    ("GJ", "Gujarat"),
    ("HR", "Haryana"),
    ("HP", "Himachal Pradesh"),
    ("JK", "Jammu and Kashmir"),
    ("JH", "Jharkhand"),
    ("KA", "Karnataka"),
    ("KL", "Kerala"),
    ("LA", "Ladakh"),
    ("LD", "Lakshadweep"),
    ("MP", "Madhya Pradesh"),
    ("MH", "Maharashtra"),
    ("MN", "Manipur"),
    ("ML", "Meghalaya"),
    ("MZ", "Mizoram"),
    ("NL", "Nagaland"),
    ("OR", "Odisha"),
    ("PY", "Puducherry"),
    ("PB", "Punjab"),
    ("RJ", "Rajasthan"),
    ("SK", "Sikkim"),
    ("TN", "Tamil Nadu"),
    ("TG", "Telangana"),
    ("TR", "Tripura"),
    ("DD", "Dadra and Nagar Haveli and Daman and Diu"),
    ("UP", "Uttar Pradesh"),
    ("UK", "Uttarakhand"),
    ("WB", "West Bengal"),
]


# ============================================================
# REPORT JOBS
# ============================================================

REPORT_JOBS = [

    {
        "name": "vehicle_category",
        "label": "Vehicle Category",
        "y_axis": "vehicleCategoryDescription",
        "x_axis": "monthWise",
        "year_mode": "chunks",
    },

    {
        "name": "fuel",
        "label": "Fuel",
        "y_axis": "vehicleFuel",
        "x_axis": "monthWise",
        "year_mode": "chunks",
    },

    {
        "name": "manufacturer",
        "label": "Manufacturer",
        "y_axis": "vehicleMakerName",
        "x_axis": "monthWise",
        "year_mode": "single",
    },

]


# ============================================================
# CREATE DIRECTORIES
# ============================================================

def create_directories():

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RAW_HTML_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# SAFE FILE NAME
# ============================================================

def safe_name(text):

    text = str(text).strip()

    text = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        text
    )

    text = re.sub(
        r"_+",
        "_",
        text
    )

    return text.strip("_")


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(value):

    if not value:
        return ""

    value = str(value)

    value = (
        value
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip().upper()


# ============================================================
# CREATE DRIVER
# ============================================================

def create_driver():

    options = Options()

    options.add_argument(
        "--start-maximized"
    )

    options.add_argument(
        "--disable-notifications"
    )

    options.add_argument(
        "--disable-popup-blocking"
    )

    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(
                DOWNLOAD_DIR.resolve()
            ),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
    )

    driver = webdriver.Chrome(
        options=options
    )

    driver.set_page_load_timeout(
        PAGE_LOAD_TIMEOUT
    )

    return driver


# ============================================================
# WAIT FOR PAGE
# ============================================================

def wait_for_page(driver):

    wait = WebDriverWait(
        driver,
        LONG_WAIT
    )

    wait.until(
        lambda d:
        d.execute_script(
            "return document.readyState"
        ) in [
            "interactive",
            "complete"
        ]
    )

    # Small wait only for dynamic controls
    time.sleep(1.5)


# ============================================================
# OPEN PORTAL
# ============================================================

def open_portal(driver):

    print("\nOpening VAHAN portal...")

    driver.get(URL)

    wait_for_page(driver)

    print("✓ VAHAN portal opened.")

    print("\nChrome is ready.")
    print("CAPTCHA will be entered manually.")

    input(
        "Press ENTER to start extraction..."
    )


# ============================================================
# GET VISIBLE SELECT
# ============================================================

def get_visible_select(
    driver,
    select_id
):

    elements = driver.find_elements(
        By.ID,
        select_id
    )

    if not elements:

        raise Exception(
            f"Select not found: {select_id}"
        )

    for element in elements:

        try:

            if element.is_displayed():
                return element

        except Exception:
            continue

    return elements[0]


# ============================================================
# GET VISIBLE INPUT
# ============================================================

def get_visible_input(
    driver,
    input_id
):

    elements = driver.find_elements(
        By.ID,
        input_id
    )

    if not elements:

        raise Exception(
            f"Input not found: {input_id}"
        )

    for element in elements:

        try:

            if element.is_displayed():
                return element

        except Exception:
            continue

    return elements[0]


# ============================================================
# SELECT NORMAL DROPDOWN BY VALUE
# ============================================================

def select_by_value(
    driver,
    select_id,
    value,
    description=""
):

    element = get_visible_select(
        driver,
        select_id
    )

    print(
        f"Selecting {select_id} = {value}"
    )

    options = element.find_elements(
        By.TAG_NAME,
        "option"
    )

    available = []

    for option in options:

        available.append(
            (
                option.get_attribute("value"),
                option.text.strip()
            )
        )

    print(
        f"Available options: {available}"
    )

    found = False

    for option in options:

        option_value = (
            option.get_attribute("value")
            or ""
        ).strip()

        if option_value == value:

            driver.execute_script(
                """
                const select = arguments[0];
                const option = arguments[1];

                for (const opt of select.options) {
                    opt.selected = false;
                }

                option.selected = true;

                select.dispatchEvent(
                    new Event(
                        'input',
                        {bubbles:true}
                    )
                );

                select.dispatchEvent(
                    new Event(
                        'change',
                        {bubbles:true}
                    )
                );
                """,
                element,
                option
            )

            found = True
            break

    if not found:

        raise Exception(
            f"Value not found in {select_id}: {value}"
        )

    # Optimized verification
    end_time = time.time() + 10

    while time.time() < end_time:

        try:

            selected_value = (
                element.get_attribute("value")
                or ""
            ).strip()

            if selected_value == value:

                print(
                    f"✓ {select_id} selected -> {value}"
                )

                return True

        except StaleElementReferenceException:

            element = get_visible_select(
                driver,
                select_id
            )

        time.sleep(0.5)

    raise Exception(
        f"{select_id} selection verification failed. "
        f"Expected={value}"
    )


# ============================================================
# WAIT FOR X-AXIS OPTION
# ============================================================

def wait_for_x_axis_option(
    driver,
    x_axis_value
):

    print(
        f"Waiting for X-Axis option: "
        f"{x_axis_value}"
    )

    end_time = time.time() + LONG_WAIT

    while time.time() < end_time:

        try:

            x_axis = get_visible_select(
                driver,
                "xAxis"
            )

            options = x_axis.find_elements(
                By.TAG_NAME,
                "option"
            )

            values = [

                (
                    option.get_attribute("value")
                    or ""
                ).strip()

                for option in options
            ]

            if x_axis_value in values:

                print(
                    f"✓ X-Axis option available: "
                    f"{x_axis_value}"
                )

                return True

        except (
            StaleElementReferenceException,
            WebDriverException
        ):
            pass

        time.sleep(0.5)

    raise TimeoutException(
        f"X-axis option not available: "
        f"{x_axis_value}"
    )


# ============================================================
# SET YEAR INPUT
# ============================================================

def set_year_input(
    driver,
    input_id,
    value
):

    value = str(value)

    print(
        f"Setting {input_id} = {value}"
    )

    end_time = time.time() + 30

    while time.time() < end_time:

        try:

            element = get_visible_input(
                driver,
                input_id
            )

            driver.execute_script(
                """
                const el = arguments[0];
                const value = arguments[1];

                el.removeAttribute('readonly');
                el.removeAttribute('disabled');

                const setter =
                    Object.getOwnPropertyDescriptor(
                        HTMLInputElement.prototype,
                        'value'
                    ).set;

                setter.call(el, value);

                el.dispatchEvent(
                    new Event(
                        'input',
                        {bubbles:true}
                    )
                );

                el.dispatchEvent(
                    new Event(
                        'change',
                        {bubbles:true}
                    )
                );

                el.dispatchEvent(
                    new Event(
                        'blur',
                        {bubbles:true}
                    )
                );

                if (window.jQuery) {

                    window.jQuery(el).trigger('input');
                    window.jQuery(el).trigger('change');
                    window.jQuery(el).trigger('blur');

                }

                el.focus();
                el.blur();
                """,
                element,
                value
            )

            time.sleep(0.5)

            actual = (
                element.get_attribute("value")
                or ""
            ).strip()

            if actual != value:
                time.sleep(0.5)
                continue

            print(
                f"✓ {input_id} changed -> {value}"
            )

            # Short stability verification
            stable_start = time.time()

            while (
                time.time() - stable_start
                < YEAR_STABLE_SECONDS
            ):

                current = (
                    element.get_attribute("value")
                    or ""
                ).strip()

                if current != value:
                    break

                time.sleep(0.3)

            else:

                print(
                    f"✓ {input_id} stable -> {value}"
                )

                return True

        except (
            StaleElementReferenceException,
            WebDriverException
        ):
            pass

        time.sleep(0.5)

    raise TimeoutException(
        f"Unable to set stable value "
        f"for {input_id}: {value}"
    )


# ============================================================
# SET YEAR RANGE
# ============================================================

def set_year_range(
    driver,
    from_year,
    to_year
):

    print("\n" + "=" * 60)
    print("SETTING YEAR RANGE")
    print("=" * 60)

    print(
        f"Requested: {from_year} - {to_year}"
    )

    set_year_input(
        driver,
        "fromYear",
        from_year
    )

    set_year_input(
        driver,
        "toYear",
        to_year
    )

    time.sleep(
        CONFIG_SETTLE_SECONDS
    )

    from_element = get_visible_input(
        driver,
        "fromYear"
    )

    to_element = get_visible_input(
        driver,
        "toYear"
    )

    actual_from = (
        from_element.get_attribute("value")
        or ""
    ).strip()

    actual_to = (
        to_element.get_attribute("value")
        or ""
    ).strip()

    print("\nFINAL CONFIGURATION")

    print(
        f"From Year   : {actual_from}"
    )

    print(
        f"To Year     : {actual_to}"
    )

    if (
        actual_from != str(from_year)
        or actual_to != str(to_year)
    ):

        raise Exception(
            "YEAR VALUES NOT VERIFIED. "
            f"Expected={from_year}-{to_year}, "
            f"Actual={actual_from}-{actual_to}"
        )

    print(
        "\n✓ YEAR VALUES VERIFIED"
    )


# ============================================================
# CONFIGURE REPORT
# ============================================================

def configure_report(
    driver,
    job,
    from_year,
    to_year
):

    print("\n" + "#" * 80)

    print(
        f"STATE      : {job['state_label']}"
    )

    print(
        f"STATE CODE : {job['state_value']}"
    )

    print(
        f"DIMENSION  : {job['label']}"
    )

    print(
        f"YEARS      : {from_year}-{to_year}"
    )

    print(
        f"Y-AXIS     : {job['y_axis']}"
    )

    print(
        f"X-AXIS     : {job['x_axis']}"
    )

    print("#" * 80)

    print("\n" + "=" * 65)
    print("CONFIGURING REPORT")
    print("=" * 65)

    # --------------------------------------------------------
    # Report type
    # --------------------------------------------------------

    select_by_value(
        driver,
        "reportType",
        REPORT_TYPE_VALUE
    )

    # --------------------------------------------------------
    # Y-axis
    # --------------------------------------------------------

    select_by_value(
        driver,
        "yAxis",
        job["y_axis"]
    )

    print(
        f"✓ Y-Axis: {job['label']}"
    )

    # Small wait for X-axis dynamic population
    time.sleep(0.8)

    # --------------------------------------------------------
    # X-axis
    # --------------------------------------------------------

    wait_for_x_axis_option(
        driver,
        job["x_axis"]
    )

    select_by_value(
        driver,
        "xAxis",
        job["x_axis"]
    )

    print(
        f"✓ X-Axis: {job['x_axis']}"
    )

    # --------------------------------------------------------
    # Years
    # --------------------------------------------------------

    set_year_range(
        driver,
        from_year,
        to_year
    )


# ============================================================
# SELECT STATE
#
# IMPORTANT:
#   State is selected ONCE per state.
#
#   Multiple fallback methods:
#   1. Exact label
#   2. Label contains
#   3. Checkbox row
#   4. Option order
#   5. Direct underlying select
#
# ============================================================

def select_state(
    driver,
    state_value,
    state_label
):

    print("\n" + "=" * 65)
    print("SELECTING STATE")
    print("=" * 65)

    print(
        f"State     : {state_label}"
    )

    print(
        f"State Code: {state_value}"
    )

    wait = WebDriverWait(
        driver,
        WAIT_TIMEOUT
    )

    target_code = normalize_text(
        state_value
    )

    target_label = normalize_text(
        state_label
    )

    # ========================================================
    # 1. REAL UNDERLYING SELECT
    # ========================================================

    state_select = wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "select#stateName"
            )
        )
    )

    options = state_select.find_elements(
        By.TAG_NAME,
        "option"
    )

    state_map = {}
    ordered_states = []

    for option in options:

        value = (
            option.get_attribute("value")
            or ""
        ).strip()

        text = (
            option.text
            or ""
        ).strip()

        if value:

            normalized_value = normalize_text(
                value
            )

            state_map[
                normalized_value
            ] = text

            ordered_states.append(
                (
                    normalized_value,
                    text
                )
            )

    print(
        f"Total available states: "
        f"{len(state_map)}"
    )

    if target_code not in state_map:

        raise Exception(
            f"State code not found: "
            f"{state_value}"
        )

    print(
        f"✓ State option found: "
        f"{state_value} | "
        f"{state_map[target_code]}"
    )

    # ========================================================
    # 2. FIND STATE DROPDOWN
    # ========================================================

    dropdowns = driver.find_elements(
        By.CSS_SELECTOR,
        "div.multiselect-dropdown"
    )

    print(
        f"State container dropdowns found: "
        f"{len(dropdowns)}"
    )

    if not dropdowns:

        raise Exception(
            "No custom multiselect dropdown found"
        )

    state_dropdown = None

    # --------------------------------------------------------
    # Best method: walk upward from state select
    # --------------------------------------------------------

    try:

        state_dropdown = driver.execute_script(
            """
            const select =
                document.querySelector(
                    'select#stateName'
                );

            if (!select) {
                return null;
            }

            let current =
                select.parentElement;

            for (
                let i = 0;
                i < 12 && current;
                i++
            ) {

                const dropdown =
                    current.querySelector(
                        'div.multiselect-dropdown'
                    );

                if (dropdown) {
                    return dropdown;
                }

                current =
                    current.parentElement;
            }

            return null;
            """
        )

    except Exception:

        state_dropdown = None

    # --------------------------------------------------------
    # Fallback: inspect dropdown text/html
    # --------------------------------------------------------

    if state_dropdown is None:

        for dropdown in dropdowns:

            try:

                html = (
                    dropdown.get_attribute(
                        "outerHTML"
                    )
                    or ""
                )

                text = (
                    dropdown.text
                    or ""
                )

                combined = (
                    html + " " + text
                ).upper()

                if (
                    "SELECT STATE" in combined
                    or "STATE" in combined
                ):

                    state_dropdown = dropdown
                    break

            except Exception:
                continue

    # --------------------------------------------------------
    # Single dropdown fallback
    # --------------------------------------------------------

    if (
        state_dropdown is None
        and len(dropdowns) == 1
    ):

        state_dropdown = dropdowns[0]

    if state_dropdown is None:

        raise Exception(
            "Correct state dropdown could "
            "not be identified"
        )

    print(
        "✓ Correct state dropdown identified."
    )

    # ========================================================
    # 3. OPEN STATE DROPDOWN
    # ========================================================

    driver.execute_script(
        """
        arguments[0].scrollIntoView({
            block: 'center'
        });
        """,
        state_dropdown
    )

    time.sleep(0.5)

    driver.execute_script(
        """
        arguments[0].click();
        """,
        state_dropdown
    )

    time.sleep(0.8)

    # ========================================================
    # 4. FIND ALL CHECKBOX ROWS
    # ========================================================

    rows = state_dropdown.find_elements(
        By.CSS_SELECTOR,
        "div[data-search-text]"
    )

    checkbox_rows = []

    try:

        all_divs = state_dropdown.find_elements(
            By.CSS_SELECTOR,
            "div"
        )

        for div in all_divs:

            try:

                checkboxes = div.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='checkbox']"
                )

                labels = div.find_elements(
                    By.TAG_NAME,
                    "label"
                )

                if (
                    checkboxes
                    and labels
                ):

                    if div not in checkbox_rows:
                        checkbox_rows.append(div)

            except Exception:
                continue

    except Exception:
        pass

    print(
        f"State dropdown rows found: "
        f"{len(rows)}"
    )

    print(
        f"Checkbox rows available: "
        f"{len(checkbox_rows)}"
    )

    # ========================================================
    # 5. FIND TARGET ROW
    # ========================================================

    target_row = None
    matched_method = None

    # --------------------------------------------------------
    # METHOD 1: Exact data-search-text
    # --------------------------------------------------------

    for row in rows:

        try:

            search_text = normalize_text(
                row.get_attribute(
                    "data-search-text"
                )
            )

            if search_text == target_label:

                target_row = row
                matched_method = (
                    "data-search-text exact"
                )

                break

        except (
            StaleElementReferenceException
        ):
            continue

    # --------------------------------------------------------
    # METHOD 2: Label exact text
    # --------------------------------------------------------

    if target_row is None:

        for row in checkbox_rows:

            try:

                labels = row.find_elements(
                    By.TAG_NAME,
                    "label"
                )

                for label in labels:

                    label_text = normalize_text(
                        label.text
                    )

                    if label_text == target_label:

                        target_row = row
                        matched_method = (
                            "label exact"
                        )

                        break

                if target_row is not None:
                    break

            except (
                StaleElementReferenceException
            ):
                continue

    # --------------------------------------------------------
    # METHOD 3: Label contains
    # --------------------------------------------------------

    if target_row is None:

        for row in checkbox_rows:

            try:

                labels = row.find_elements(
                    By.TAG_NAME,
                    "label"
                )

                for label in labels:

                    label_text = normalize_text(
                        label.text
                    )

                    if (
                        target_label in label_text
                        or label_text in target_label
                    ):

                        target_row = row
                        matched_method = (
                            "label contains"
                        )

                        break

                if target_row is not None:
                    break

            except Exception:
                continue

    # --------------------------------------------------------
    # METHOD 4: Row text
    # --------------------------------------------------------

    if target_row is None:

        for row in checkbox_rows:

            try:

                row_text = normalize_text(
                    row.text
                )

                if (
                    target_label in row_text
                    or row_text in target_label
                ):

                    target_row = row
                    matched_method = (
                        "row text"
                    )

                    break

            except Exception:
                continue

    # --------------------------------------------------------
    # METHOD 5: State code attribute
    # --------------------------------------------------------

    if target_row is None:

        for row in checkbox_rows:

            try:

                html = (
                    row.get_attribute(
                        "outerHTML"
                    )
                    or ""
                ).upper()

                patterns = [

                    f'value="{target_code}"',
                    f"value='{target_code}'",

                    f'data-value="{target_code}"',
                    f"data-value='{target_code}'",

                    f'data-code="{target_code}"',
                    f"data-code='{target_code}'",

                    f'id="{target_code}"',
                    f"id='{target_code}'",
                ]

                if any(
                    pattern.upper()
                    in html
                    for pattern in patterns
                ):

                    target_row = row
                    matched_method = (
                        "state code attribute"
                    )

                    break

            except Exception:
                continue

    # --------------------------------------------------------
    # METHOD 6: Option order fallback
    # --------------------------------------------------------

    if target_row is None:

        target_index = None

        for index, (
            value,
            text
        ) in enumerate(
            ordered_states
        ):

            if value == target_code:

                target_index = index
                break

        if target_index is not None:

            if (
                target_index
                < len(checkbox_rows)
            ):

                target_row = (
                    checkbox_rows[
                        target_index
                    ]
                )

                matched_method = (
                    "option order"
                )

    # ========================================================
    # 6. CLICK / SET TARGET STATE
    # ========================================================

    if target_row is not None:

        print(
            f"✓ State matched using "
            f"{matched_method}"
        )

        try:

            checkbox = None
            label_element = None

            checkboxes = target_row.find_elements(
                By.CSS_SELECTOR,
                "input[type='checkbox']"
            )

            if checkboxes:
                checkbox = checkboxes[0]

            labels = target_row.find_elements(
                By.TAG_NAME,
                "label"
            )

            if labels:
                label_element = labels[0]

            # ------------------------------------------------
            # First try label click
            # ------------------------------------------------

            if label_element is not None:

                driver.execute_script(
                    """
                    arguments[0].scrollIntoView({
                        block: 'center'
                    });

                    arguments[0].click();
                    """,
                    label_element
                )

                time.sleep(0.8)

            # ------------------------------------------------
            # Then checkbox if required
            # ------------------------------------------------

            if (
                checkbox is not None
                and not checkbox.is_selected()
            ):

                driver.execute_script(
                    """
                    arguments[0].click();

                    arguments[0].dispatchEvent(
                        new Event(
                            'input',
                            {bubbles:true}
                        )
                    );

                    arguments[0].dispatchEvent(
                        new Event(
                            'change',
                            {bubbles:true}
                        )
                    );
                    """,
                    checkbox
                )

                time.sleep(0.8)

        except Exception as click_error:

            print(
                "⚠ Custom checkbox click "
                f"problem: {click_error}"
            )

    # ========================================================
    # 7. DIRECT UNDERLYING SELECT FALLBACK
    #
    # This is especially useful when custom UI checkbox
    # click does not update the real select.
    # ========================================================

    print(
        "\nVerifying underlying state select..."
    )

    try:

        state_select = get_visible_select(
            driver,
            "stateName"
        )

        # Make sure ONLY target state is selected.
        driver.execute_script(
            """
            const select = arguments[0];
            const target = arguments[1];

            for (
                const option of select.options
            ) {
                option.selected =
                    (
                        option.value || ''
                    ).trim().toUpperCase()
                    === target;
            }

            select.dispatchEvent(
                new Event(
                    'input',
                    {bubbles:true}
                )
            );

            select.dispatchEvent(
                new Event(
                    'change',
                    {bubbles:true}
                )
            );

            if (window.jQuery) {

                window.jQuery(select)
                    .trigger('input');

                window.jQuery(select)
                    .trigger('change');
            }
            """,
            state_select,
            target_code
        )

        time.sleep(0.8)

    except Exception as direct_error:

        print(
            "⚠ Direct select fallback warning: "
            f"{direct_error}"
        )

    # ========================================================
    # 8. VERIFY SELECTED STATES
    # ========================================================

    selected_values = driver.execute_script(
        """
        const select =
            document.querySelector(
                'select#stateName'
            );

        if (!select) {
            return [];
        }

        return Array.from(
            select.options
        )
        .filter(
            option => option.selected
        )
        .map(
            option =>
                (
                    option.value || ''
                ).trim()
        );
        """
    )

    selected_values = [
        normalize_text(value)
        for value in selected_values
    ]

    print(
        "\nSelected states:"
    )

    for value in selected_values:

        label = state_map.get(
            value,
            ""
        )

        print(
            f"  {value} | {label}"
        )

    # ========================================================
    # FINAL VERIFICATION
    # ========================================================

    if (
        len(selected_values) != 1
        or target_code not in selected_values
    ):

        raise Exception(
            "State selection verification failed. "
            f"Expected ONLY {state_value}, "
            f"Actual={selected_values}"
        )

    print(
        f"\n✓ STATE SELECTED: "
        f"{state_label} ({state_value})"
    )

    # ========================================================
    # CLOSE DROPDOWN
    # ========================================================

    try:

        driver.execute_script(
            """
            document.body.click();
            """
        )

    except Exception:
        pass

    time.sleep(0.4)

    return True


# ============================================================
# CAPTCHA CHECKPOINT
# ============================================================

def captcha_checkpoint(
    state_label,
    dimension,
    from_year,
    to_year
):

    print("\n" + "=" * 70)
    print("CAPTCHA CHECKPOINT")
    print("=" * 70)

    print(
        f"State     : {state_label}"
    )

    print(
        f"Dimension : {dimension}"
    )

    print(
        f"Years     : {from_year}-{to_year}"
    )

    print(
        "\nPlease solve the CAPTCHA manually "
        "in Chrome."
    )

    input(
        "After CAPTCHA is completed, press ENTER..."
    )


# ============================================================
# CLICK APPLY
# ============================================================

def click_apply(driver):

    print(
        "\nClicking Apply..."
    )

    selectors = [

        (
            By.ID,
            "applyBtn"
        ),

        (
            By.CSS_SELECTOR,
            "button[type='submit']"
        ),

        (
            By.XPATH,
            "//button[contains("
            "translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),"
            "'apply')]"
        ),

        (
            By.XPATH,
            "//input[@type='button' and "
            "contains("
            "translate(@value,"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),"
            "'apply')]"
        ),
    ]

    for selector in selectors:

        try:

            elements = driver.find_elements(
                *selector
            )

            for element in elements:

                try:

                    if element.is_displayed():

                        driver.execute_script(
                            """
                            arguments[0]
                                .scrollIntoView({
                                    block: 'center'
                                });
                            """,
                            element
                        )

                        time.sleep(0.3)

                        driver.execute_script(
                            """
                            arguments[0].click();
                            """,
                            element
                        )

                        print(
                            "✓ Apply clicked."
                        )

                        return True

                except Exception:
                    continue

        except Exception:
            continue

    raise Exception(
        "Apply button not found"
    )


# ============================================================
# WAIT FOR TABLE
# ============================================================

def wait_for_table(driver):

    print(
        "Waiting for report table..."
    )

    end_time = time.time() + LONG_WAIT

    while time.time() < end_time:

        try:

            tables = driver.find_elements(
                By.TAG_NAME,
                "table"
            )

            for table in tables:

                try:

                    if table.is_displayed():

                        rows = table.find_elements(
                            By.TAG_NAME,
                            "tr"
                        )

                        if len(rows) >= 2:

                            print(
                                "✓ Report table detected."
                            )

                            return True

                except Exception:
                    continue

        except Exception:
            pass

        time.sleep(1)

    raise TimeoutException(
        "Report table not detected."
    )


# ============================================================
# SAVE HTML
# ============================================================

def save_html(
    driver,
    filename
):

    path = (
        RAW_HTML_DIR
        / filename
    )

    html = driver.page_source

    path.write_text(
        html,
        encoding="utf-8"
    )

    print(
        f"HTML saved:\n{path}"
    )

    return path


# ============================================================
# CLEAR DOWNLOAD FOLDER
# ============================================================

def clear_download_folder():

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

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

def find_download_button(driver):

    # --------------------------------------------------------
    # Method 1
    # --------------------------------------------------------

    try:

        buttons = driver.find_elements(
            By.ID,
            "downloadBtn"
        )

        for button in buttons:

            try:

                if button.is_displayed():
                    return button

            except Exception:
                continue

    except Exception:
        pass

    # --------------------------------------------------------
    # Method 2
    # --------------------------------------------------------

    xpath_list = [

        "//button[contains("
        "translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),"
        "'download all records csv')]",

        "//a[contains("
        "translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),"
        "'download all records csv')]",

        "//*[contains("
        "translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),"
        "'download all records csv')]",
    ]

    for xpath in xpath_list:

        try:

            elements = driver.find_elements(
                By.XPATH,
                xpath
            )

            for element in elements:

                try:

                    if element.is_displayed():
                        return element

                except Exception:
                    continue

        except Exception:
            continue

    return None


# ============================================================
# CLICK DOWNLOAD
# ============================================================

def click_download(driver):

    print(
        "\nSearching for download button..."
    )

    end_time = time.time() + 60

    while time.time() < end_time:

        button = find_download_button(
            driver
        )

        if button is not None:

            try:

                driver.execute_script(
                    """
                    arguments[0].scrollIntoView({
                        block: 'center'
                    });
                    """,
                    button
                )

                time.sleep(0.3)

                driver.execute_script(
                    """
                    arguments[0].click();
                    """,
                    button
                )

                print(
                    "✓ Download clicked."
                )

                return True

            except Exception:
                pass

        time.sleep(1)

    raise TimeoutException(
        "Download button not found."
    )


# ============================================================
# WAIT FOR CSV
# ============================================================

def wait_for_csv():

    print(
        "Waiting for CSV download..."
    )

    end_time = (
        time.time()
        + DOWNLOAD_TIMEOUT
    )

    while time.time() < end_time:

        files = list(
            DOWNLOAD_DIR.glob("*")
        )

        csv_files = [

            file

            for file in files

            if (
                file.is_file()
                and file.suffix.lower() == ".csv"
            )
        ]

        temporary_files = [

            file

            for file in files

            if (
                file.suffix.lower()
                in [
                    ".crdownload",
                    ".tmp"
                ]
            )
        ]

        if (
            csv_files
            and not temporary_files
        ):

            csv_files.sort(
                key=lambda f:
                f.stat().st_mtime,
                reverse=True
            )

            csv_file = csv_files[0]

            size1 = (
                csv_file.stat().st_size
            )

            time.sleep(1)

            size2 = (
                csv_file.stat().st_size
            )

            if size1 == size2:

                print(
                    f"✓ CSV downloaded:\n"
                    f"{csv_file}"
                )

                return csv_file

        time.sleep(1)

    raise TimeoutException(
        "CSV download timeout."
    )


# ============================================================
# SAVE CSV
# ============================================================

def save_csv(
    downloaded_file,
    output_path
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if output_path.exists():
        output_path.unlink()

    shutil.move(
        str(downloaded_file),
        str(output_path)
    )

    print(
        f"CSV saved:\n{output_path}"
    )

    return output_path


# ============================================================
# LOG RESULT
# ============================================================

def log_result(
    state_value,
    state_label,
    job_name,
    dimension,
    from_year,
    to_year,
    status,
    message=""
):

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_exists = LOG_FILE.exists()

    with LOG_FILE.open(
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:

            writer.writerow([
                "timestamp",
                "state_code",
                "state",
                "job",
                "dimension",
                "from_year",
                "to_year",
                "status",
                "message",
            ])

        writer.writerow([
            datetime.now().isoformat(
                timespec="seconds"
            ),
            state_value,
            state_label,
            job_name,
            dimension,
            from_year,
            to_year,
            status,
            message,
        ])


# ============================================================
# OUTPUT PATH
# ============================================================

def get_output_path(
    state_value,
    job,
    from_year,
    to_year
):

    return (
        RAW_DIR
        /
        (
            f"vahan_"
            f"{job['name']}_"
            f"{state_value.lower()}_"
            f"monthwise_"
            f"{from_year}_"
            f"{to_year}.csv"
        )
    )


# ============================================================
# HTML OUTPUT PATH
# ============================================================

def get_html_path(
    state_value,
    job,
    from_year,
    to_year
):

    return (
        RAW_HTML_DIR
        /
        (
            f"vahan_"
            f"{job['name']}_"
            f"{state_value.lower()}_"
            f"{from_year}_"
            f"{to_year}.html"
        )
    )


# ============================================================
# FAILURE HTML PATH
# ============================================================

def get_failure_html_path(
    state_value,
    job,
    from_year,
    to_year
):

    return (
        RAW_HTML_DIR
        /
        (
            f"FAILED_"
            f"{state_value.lower()}_"
            f"{job['name']}_"
            f"{from_year}_"
            f"{to_year}.html"
        )
    )


# ============================================================
# CHECK EXISTING OUTPUT
# ============================================================

def output_exists(path):

    return (
        path.exists()
        and path.stat().st_size > 0
    )


# ============================================================
# BUILD REPORT PLAN
# ============================================================

def build_report_plan():

    reports = []

    for state_value, state_label in STATES:

        for job in REPORT_JOBS:

            if job["year_mode"] == "chunks":

                for from_year, to_year in YEAR_CHUNKS:

                    report = job.copy()

                    report["state_value"] = (
                        state_value
                    )

                    report["state_label"] = (
                        state_label
                    )

                    report["from_year"] = (
                        from_year
                    )

                    report["to_year"] = (
                        to_year
                    )

                    reports.append(
                        report
                    )

            elif job["year_mode"] == "single":

                for year in range(
                    2016,
                    2027
                ):

                    report = job.copy()

                    report["state_value"] = (
                        state_value
                    )

                    report["state_label"] = (
                        state_label
                    )

                    report["from_year"] = (
                        year
                    )

                    report["to_year"] = (
                        year
                    )

                    reports.append(
                        report
                    )

    return reports


# ============================================================
# PRINT PLAN
# ============================================================

def print_plan(reports):

    category_count = 36 * 4
    fuel_count = 36 * 4
    manufacturer_count = 36 * 11

    print(
        "\n" + "=" * 80
    )

    print(
        "VAHAN STATE-WISE MASTER EXTRACTION"
    )

    print(
        "OPTIMIZED STATE-BATCH MODE"
    )

    print(
        "=" * 80
    )

    print(
        f"\nTotal planned reports: "
        f"{len(reports)}"
    )

    print(
        "\nVehicle Category:"
    )

    print(
        f"36 states × 4 chunks = "
        f"{category_count}"
    )

    print(
        "\nFuel:"
    )

    print(
        f"36 states × 4 chunks = "
        f"{fuel_count}"
    )

    print(
        "\nManufacturer:"
    )

    print(
        f"36 states × 11 years = "
        f"{manufacturer_count}"
    )

    print(
        "\nTOTAL:"
    )

    print(
        f"{category_count} + "
        f"{fuel_count} + "
        f"{manufacturer_count} = "
        f"{len(reports)} reports"
    )

    print(
        "\nOptimization:"
    )

    print(
        "✓ Page reload: once per state"
    )

    print(
        "✓ State selection: once per state"
    )

    print(
        "✓ CAPTCHA: manual"
    )

    print(
        "✓ Existing outputs: skipped"
    )

    print(
        "\n" + "=" * 80
    )


# ============================================================
# EXTRACT ONE REPORT
#
# IMPORTANT:
#   This function DOES NOT reload the page.
#   State is already selected by the state-batch loop.
# ============================================================

def extract_report(
    driver,
    report,
    report_number,
    total_reports
):

    state_value = report[
        "state_value"
    ]

    state_label = report[
        "state_label"
    ]

    from_year = report[
        "from_year"
    ]

    to_year = report[
        "to_year"
    ]

    output_path = get_output_path(
        state_value,
        report,
        from_year,
        to_year
    )

    html_path = get_html_path(
        state_value,
        report,
        from_year,
        to_year
    )

    # ========================================================
    # JOB HEADER
    # ========================================================

    print("\n" + "#" * 80)

    print(
        f"JOB {report_number}/{total_reports}"
    )

    print(
        f"State     : {state_label}"
    )

    print(
        f"Dimension : {report['label']}"
    )

    print(
        f"Years     : {from_year}-{to_year}"
    )

    print("#" * 80)

    # ========================================================
    # SKIP EXISTING
    # ========================================================

    if output_exists(output_path):

        print(
            "\n✓ OUTPUT ALREADY EXISTS"
        )

        print(
            output_path
        )

        log_result(
            state_value,
            state_label,
            report["name"],
            report["label"],
            from_year,
            to_year,
            "SKIPPED",
            "Output already exists"
        )

        return "skipped"

    # ========================================================
    # CONFIGURE REPORT
    # ========================================================

    configure_report(
        driver,
        report,
        from_year,
        to_year
    )

    # ========================================================
    # IMPORTANT:
    # State is NOT selected here.
    #
    # It was selected once before state batch started.
    # ========================================================

    # ========================================================
    # CAPTCHA
    # ========================================================

    captcha_checkpoint(
        state_label,
        report["label"],
        from_year,
        to_year
    )

    # ========================================================
    # APPLY
    # ========================================================

    click_apply(
        driver
    )

    # ========================================================
    # WAIT TABLE
    # ========================================================

    wait_for_table(
        driver
    )

    # ========================================================
    # SAVE HTML
    # ========================================================

    save_html(
        driver,
        html_path.name
    )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    clear_download_folder()

    click_download(
        driver
    )

    downloaded_file = wait_for_csv()

    # ========================================================
    # SAVE CSV
    # ========================================================

    save_csv(
        downloaded_file,
        output_path
    )

    # ========================================================
    # LOG SUCCESS
    # ========================================================

    log_result(
        state_value,
        state_label,
        report["name"],
        report["label"],
        from_year,
        to_year,
        "SUCCESS",
        ""
    )

    print(
        "\n✓ SUCCESS"
    )

    return "success"


# ============================================================
# MAIN
# ============================================================

def main():

    create_directories()

    reports = build_report_plan()

    print_plan(
        reports
    )

    driver = None

    successful = 0
    skipped = 0
    failed = 0

    try:

        # ====================================================
        # CREATE DRIVER
        # ====================================================

        driver = create_driver()

        # ====================================================
        # OPEN PORTAL ONCE
        # ====================================================

        open_portal(
            driver
        )

        # ====================================================
        # PROCESS STATE BY STATE
        #
        # This is the main optimization.
        # ====================================================

        total_reports = len(reports)

        report_index = 0

        state_groups = {}

        for report in reports:

            state_value = report[
                "state_value"
            ]

            if state_value not in state_groups:

                state_groups[
                    state_value
                ] = []

            state_groups[
                state_value
            ].append(report)

        # ====================================================
        # STATE LOOP
        # ====================================================

        for state_value, state_reports in (
            state_groups.items()
        ):

            state_label = state_reports[0][
                "state_label"
            ]

            print(
                "\n\n" + "=" * 80
            )

            print(
                f"STARTING STATE: "
                f"{state_label} "
                f"({state_value})"
            )

            print(
                "=" * 80
            )

            # =================================================
            # Check whether this state has work
            # =================================================

            pending_reports = []

            for report in state_reports:

                output_path = get_output_path(
                    state_value,
                    report,
                    report["from_year"],
                    report["to_year"]
                )

                if not output_exists(
                    output_path
                ):

                    pending_reports.append(
                        report
                    )

                else:

                    print(
                        f"Already exists: "
                        f"{output_path.name}"
                    )

            # =================================================
            # If all state outputs exist
            # =================================================

            if not pending_reports:

                print(
                    f"\n✓ ALL REPORTS ALREADY "
                    f"EXIST FOR {state_label}"
                )

                for report in state_reports:

                    report_index += 1
                    skipped += 1

                    log_result(
                        state_value,
                        state_label,
                        report["name"],
                        report["label"],
                        report["from_year"],
                        report["to_year"],
                        "SKIPPED",
                        "Output already exists"
                    )

                continue

            # =================================================
            # STATE PAGE LOAD
            #
            # ONLY ONCE FOR THIS STATE
            # =================================================

            print(
                "\nLoading VAHAN page "
                "for new state..."
            )

            driver.get(URL)

            wait_for_page(
                driver
            )

            print(
                "✓ VAHAN page loaded."
            )

            # =================================================
            # SELECT STATE ONLY ONCE
            # =================================================

            try:

                select_state(
                    driver,
                    state_value,
                    state_label
                )

            except Exception as state_error:

                print(
                    "\n✗ STATE SELECTION FAILED"
                )

                print(
                    f"State: {state_label}"
                )

                print(
                    f"Error: {state_error}"
                )

                # Mark all pending reports for this state
                # as failed, then continue to next state.

                for report in pending_reports:

                    report_index += 1
                    failed += 1

                    error_message = str(
                        state_error
                    )

                    log_result(
                        state_value,
                        state_label,
                        report["name"],
                        report["label"],
                        report["from_year"],
                        report["to_year"],
                        "FAILED",
                        error_message
                    )

                continue

            print(
                "\n✓ STATE READY"
            )

            print(
                f"State {state_label} will now "
                f"process {len(pending_reports)} reports."
            )

            # =================================================
            # REPORTS FOR THIS STATE
            # =================================================

            for report in pending_reports:

                report_index += 1

                try:

                    result = extract_report(
                        driver,
                        report,
                        report_index,
                        total_reports
                    )

                    if result == "success":
                        successful += 1

                    elif result == "skipped":
                        skipped += 1

                except Exception as e:

                    failed += 1

                    error_message = str(e)

                    print(
                        "\n✗ FAILED"
                    )

                    print(
                        f"ERROR: "
                        f"{error_message}"
                    )

                    # -----------------------------------------
                    # Save failure HTML
                    # -----------------------------------------

                    try:

                        failure_path = (
                            get_failure_html_path(
                                state_value,
                                report,
                                report[
                                    "from_year"
                                ],
                                report[
                                    "to_year"
                                ]
                            )
                        )

                        failure_path.write_text(
                            driver.page_source,
                            encoding="utf-8"
                        )

                        print(
                            f"Failure HTML saved:\n"
                            f"{failure_path}"
                        )

                    except Exception as html_error:

                        print(
                            "Could not save failure HTML:"
                        )

                        print(
                            html_error
                        )

                    # -----------------------------------------
                    # Log failure
                    # -----------------------------------------

                    log_result(
                        state_value,
                        state_label,
                        report["name"],
                        report["label"],
                        report["from_year"],
                        report["to_year"],
                        "FAILED",
                        error_message
                    )

                    # -----------------------------------------
                    # IMPORTANT:
                    # Continue to next report.
                    # Do NOT reload page here automatically.
                    #
                    # If one report fails, next report gets
                    # a fresh configuration on same state page.
                    # -----------------------------------------

                # =================================================
                # PROGRESS
                # =================================================

                print(
                    "\n" + "=" * 65
                )

                print(
                    f"Progress : "
                    f"{report_index}/{total_reports}"
                )

                print(
                    f"Success  : "
                    f"{successful}"
                )

                print(
                    f"Skipped  : "
                    f"{skipped}"
                )

                print(
                    f"Failed   : "
                    f"{failed}"
                )

                print(
                    "=" * 65
                )

                # Very small gap
                if (
                    report_index
                    < total_reports
                ):

                    time.sleep(0.5)

            # =================================================
            # STATE COMPLETED
            # =================================================

            print(
                "\n" + "=" * 80
            )

            print(
                f"STATE COMPLETED: "
                f"{state_label} ({state_value})"
            )

            print(
                f"Reports in state: "
                f"{len(state_reports)}"
            )

            print(
                "=" * 80
            )

    except KeyboardInterrupt:

        print(
            "\n\nExtraction interrupted "
            "manually by user."
        )

    except Exception as e:

        print(
            "\n\nMASTER EXTRACTION ERROR:"
        )

        print(
            e
        )

    finally:

        print(
            "\n\n" + "=" * 80
        )

        print(
            "VAHAN STATE-WISE MASTER "
            "EXTRACTION COMPLETED"
        )

        print(
            "=" * 80
        )

        print(
            f"Total planned : "
            f"{len(reports)}"
        )

        print(
            f"Successful    : "
            f"{successful}"
        )

        print(
            f"Skipped       : "
            f"{skipped}"
        )

        print(
            f"Failed        : "
            f"{failed}"
        )

        print(
            "\nCSV folder:"
        )

        print(
            RAW_DIR
        )

        print(
            "\nHTML folder:"
        )

        print(
            RAW_HTML_DIR
        )

        print(
            "\nLog file:"
        )

        print(
            LOG_FILE
        )

        print(
            "\n" + "=" * 80
        )

        if driver is not None:

            input(
                "\nPress ENTER to close Chrome..."
            )

            try:

                driver.quit()

            except Exception:
                pass


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()