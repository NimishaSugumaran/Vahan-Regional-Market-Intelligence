from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from pathlib import Path


# =========================================================
# CONFIG
# =========================================================

URL = "https://analytics.parivahan.gov.in/analytics/vahanpublicreport?lang=en"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_HTML_DIR = DATA_DIR / "raw_html"
DOWNLOAD_DIR = DATA_DIR / "_downloads"

RAW_DIR.mkdir(parents=True, exist_ok=True)
RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


FROM_YEAR = "2016"
TO_YEAR = "2018"

OUTPUT_CSV = (
    RAW_DIR /
    "vahan_ALL_STATES_vehicle_category_monthwise_2016_2018.csv"
)

OUTPUT_HTML = (
    RAW_HTML_DIR /
    "vahan_ALL_STATES_vehicle_category_monthwise_2016_2018.html"
)


# =========================================================
# DRIVER
# =========================================================

driver = webdriver.Chrome()

wait = WebDriverWait(driver, 30)


try:

    print("=" * 80)
    print("VAHAN ALL-STATES EXTRACTION TEST")
    print("=" * 80)

    print("\nTEST CONFIGURATION:")
    print("Report Type : Calendar Year")
    print("Y Axis      : Vehicle Category")
    print("X Axis      : Month Wise")
    print("States      : ALL 36 STATES")
    print("Period      : 2016-2018")
    print("CAPTCHA     : MANUAL")

    # =====================================================
    # 1. OPEN PORTAL
    # =====================================================

    driver.get(URL)

    wait.until(
        lambda d:
        d.execute_script(
            "return document.readyState"
        ) == "complete"
    )

    time.sleep(3)

    print("\n✓ VAHAN portal opened.")

    print(
        "\nIf CAPTCHA is visible, complete it manually."
    )

    input(
        "Press ENTER when page is ready... "
    )


    # =====================================================
    # 2. REPORT TYPE
    # =====================================================

    print("\nSelecting Report Type...")

    report_type = wait.until(
        EC.presence_of_element_located(
            (By.ID, "reportType")
        )
    )

    Select(report_type).select_by_value("0")

    print(
        "✓ reportType selected -> 0 (Calendar Year)"
    )

    time.sleep(2)


    # =====================================================
    # 3. Y AXIS
    # =====================================================

    print("\nSelecting Y Axis...")

    y_axis = wait.until(
        EC.presence_of_element_located(
            (By.ID, "yAxis")
        )
    )

    Select(y_axis).select_by_value(
        "vehicleCategoryDescription"
    )

    print(
        "✓ yAxis selected -> "
        "vehicleCategoryDescription"
    )


    # =====================================================
    # 4. WAIT FOR X AXIS
    # =====================================================

    print("\nWaiting for X-axis...")

    def monthwise_available(driver):

        try:

            x_axis = driver.find_element(
                By.ID,
                "xAxis"
            )

            options = x_axis.find_elements(
                By.TAG_NAME,
                "option"
            )

            values = [
                option.get_attribute("value")
                for option in options
            ]

            return "monthWise" in values

        except Exception:

            return False


    wait.until(monthwise_available)

    print(
        "✓ monthWise available in X-axis"
    )


    # =====================================================
    # 5. SELECT MONTH WISE
    # =====================================================

    x_axis = driver.find_element(
        By.ID,
        "xAxis"
    )

    Select(x_axis).select_by_value(
        "monthWise"
    )

    print(
        "✓ xAxis selected -> monthWise"
    )

    time.sleep(2)


    # =====================================================
    # 6. YEAR INPUT
    # =====================================================

    print("\nSetting Year Range...")

    from_year = wait.until(
        EC.presence_of_element_located(
            (By.ID, "fromYear")
        )
    )

    to_year = wait.until(
        EC.presence_of_element_located(
            (By.ID, "toYear")
        )
    )


    # Remove readonly if present
    driver.execute_script(
        """
        arguments[0].removeAttribute('readonly');
        arguments[0].removeAttribute('disabled');
        """,
        from_year
    )

    driver.execute_script(
        """
        arguments[0].removeAttribute('readonly');
        arguments[0].removeAttribute('disabled');
        """,
        to_year
    )


    # Set From Year
    driver.execute_script(
        """
        const input = arguments[0];
        const value = arguments[1];

        const setter =
            Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype,
                'value'
            ).set;

        setter.call(input, value);

        input.dispatchEvent(
            new Event('input', {bubbles:true})
        );

        input.dispatchEvent(
            new Event('change', {bubbles:true})
        );

        input.dispatchEvent(
            new Event('blur', {bubbles:true})
        );
        """,
        from_year,
        FROM_YEAR
    )


    # Set To Year
    driver.execute_script(
        """
        const input = arguments[0];
        const value = arguments[1];

        const setter =
            Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype,
                'value'
            ).set;

        setter.call(input, value);

        input.dispatchEvent(
            new Event('input', {bubbles:true})
        );

        input.dispatchEvent(
            new Event('change', {bubbles:true})
        );

        input.dispatchEvent(
            new Event('blur', {bubbles:true})
        );
        """,
        to_year,
        TO_YEAR
    )


    # Verify values
    wait.until(
        lambda d:
        d.find_element(
            By.ID,
            "fromYear"
        ).get_attribute("value") == FROM_YEAR
    )

    wait.until(
        lambda d:
        d.find_element(
            By.ID,
            "toYear"
        ).get_attribute("value") == TO_YEAR
    )


    print(
        f"✓ From Year = {FROM_YEAR}"
    )

    print(
        f"✓ To Year = {TO_YEAR}"
    )

    time.sleep(3)


    # =====================================================
    # 7. FIND STATE SELECT
    # =====================================================

    print("\n" + "=" * 80)
    print("STATE DROPDOWN")
    print("=" * 80)


    state = wait.until(
        EC.presence_of_element_located(
            (By.ID, "stateName")
        )
    )


    print(
        "\nTAG      :",
        state.tag_name
    )

    print(
        "ID       :",
        state.get_attribute("id")
    )

    print(
        "NAME     :",
        state.get_attribute("name")
    )

    print(
        "MULTIPLE :",
        state.get_attribute("multiple")
    )


    # =====================================================
    # 8. GET STATES
    # =====================================================

    options = state.find_elements(
        By.TAG_NAME,
        "option"
    )


    print(
        "\nTotal available states:",
        len(options)
    )


    if len(options) != 36:

        raise Exception(
            f"Expected 36 states but found "
            f"{len(options)}"
        )


    # =====================================================
    # 9. FIND CUSTOM MULTISELECT
    # =====================================================

    print(
        "\nFinding custom State dropdown..."
    )


    state_container = state.find_element(
        By.XPATH,
        ".."
    )


    custom_dropdown = state_container.find_element(
        By.CSS_SELECTOR,
        "div.multiselect-dropdown"
    )


    print(
        "✓ Custom State dropdown found."
    )


    # =====================================================
    # 10. OPEN DROPDOWN
    # =====================================================

    print(
        "\nOpening State dropdown..."
    )


    placeholder = custom_dropdown.find_element(
        By.CSS_SELECTOR,
        "span.placeholder"
    )


    driver.execute_script(
        "arguments[0].click();",
        placeholder
    )


    time.sleep(1)


    print(
        "✓ State dropdown opened."
    )


    # =====================================================
    # 11. SELECT ALL
    # =====================================================

    print("\n" + "=" * 80)
    print("SELECTING ALL 36 STATES")
    print("=" * 80)


    checkboxes = custom_dropdown.find_elements(
        By.CSS_SELECTOR,
        "input[type='checkbox']"
    )


    print(
        "\nTotal checkboxes found:",
        len(checkboxes)
    )


    if not checkboxes:

        raise Exception(
            "No checkboxes found."
        )


    # First checkbox = Select All
    select_all_checkbox = checkboxes[0]


    print(
        "\nClicking Select All..."
    )


    driver.execute_script(
        "arguments[0].click();",
        select_all_checkbox
    )


    time.sleep(2)


    print(
        "✓ Select All clicked."
    )


    # =====================================================
    # 12. TRIGGER CHANGE
    # =====================================================

    driver.execute_script(
        """
        const element = arguments[0];

        element.dispatchEvent(
            new Event('change', {
                bubbles: true
            })
        );
        """,
        state
    )


    time.sleep(2)


    # =====================================================
    # 13. VERIFY ALL STATES
    # =====================================================

    print("\n" + "=" * 80)
    print("VERIFYING STATES")
    print("=" * 80)


    state = driver.find_element(
        By.ID,
        "stateName"
    )


    selected = state.find_elements(
        By.CSS_SELECTOR,
        "option:checked"
    )


    print(
        "\nTotal selected states:",
        len(selected)
    )


    if len(selected) != 36:

        raise Exception(
            f"Expected 36 selected states "
            f"but found {len(selected)}"
        )


    print(
        "✓ All 36 states selected."
    )


    # =====================================================
    # 14. FINAL CONFIGURATION CHECK
    # =====================================================

    print("\n" + "=" * 80)
    print("FINAL CONFIGURATION")
    print("=" * 80)


    print(
        "\nReport Type : Calendar Year"
    )

    print(
        "Y Axis      : Vehicle Category"
    )

    print(
        "X Axis      : Month Wise"
    )

    print(
        f"From Year   : {FROM_YEAR}"
    )

    print(
        f"To Year     : {TO_YEAR}"
    )

    print(
        "States      : ALL 36"
    )


    # =====================================================
    # 15. CAPTCHA
    # =====================================================

    print("\n" + "=" * 80)
    print("CAPTCHA CHECKPOINT")
    print("=" * 80)

    print(
        "\nComplete CAPTCHA manually in Chrome."
    )

    input(
        "After CAPTCHA is completed, "
        "press ENTER here... "
    )


    # =====================================================
    # 16. APPLY
    # =====================================================

    print("\n" + "=" * 80)
    print("APPLYING REPORT")
    print("=" * 80)


    apply_button = None


    # Search button by text
    buttons = driver.find_elements(
        By.XPATH,
        "//button"
    )


    for button in buttons:

        try:

            text = button.text.strip().lower()

            if "apply" in text:

                apply_button = button
                break

        except:
            continue


    # Fallback IDs
    if apply_button is None:

        for button_id in [
            "applyBtn",
            "apply",
            "submitBtn"
        ]:

            try:

                apply_button = driver.find_element(
                    By.ID,
                    button_id
                )

                break

            except:
                continue


    if apply_button is None:

        raise Exception(
            "Apply button not found."
        )


    driver.execute_script(
        "arguments[0].click();",
        apply_button
    )


    print(
        "✓ Apply clicked."
    )


    # =====================================================
    # 17. WAIT FOR REPORT TABLE
    # =====================================================

    print(
        "\nWaiting for report table..."
    )


    end_time = time.time() + 120

    table_found = False


    while time.time() < end_time:

        try:

            tables = driver.find_elements(
                By.TAG_NAME,
                "table"
            )


            for table in tables:

                if table.is_displayed():

                    rows = table.find_elements(
                        By.TAG_NAME,
                        "tr"
                    )


                    if len(rows) > 1:

                        table_found = True

                        print(
                            f"✓ Report table detected "
                            f"({len(rows)} rows)"
                        )

                        break


            if table_found:

                break


        except:
            pass


        time.sleep(2)


    if not table_found:

        raise Exception(
            "Report table not detected."
        )


    # =====================================================
    # 18. SAVE HTML
    # =====================================================

    html = driver.page_source


    OUTPUT_HTML.write_text(
        html,
        encoding="utf-8"
    )


    print(
        "\n✓ HTML saved:"
    )

    print(
        OUTPUT_HTML
    )


    # =====================================================
    # 19. FIND DOWNLOAD BUTTON
    # =====================================================

    print(
        "\nFinding Download CSV button..."
    )


    download_button = None


    try:

        button = driver.find_element(
            By.ID,
            "downloadBtn"
        )

        if button.is_displayed():

            download_button = button

    except:
        pass


    # Fallback text search
    if download_button is None:

        elements = driver.find_elements(
            By.XPATH,
            "//*[contains("
            "translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),"
            "'download all records csv'"
            ")]"
        )


        for element in elements:

            try:

                if element.is_displayed():

                    download_button = element
                    break

            except:
                continue


    if download_button is None:

        raise Exception(
            "Download CSV button not found."
        )


    # =====================================================
    # 20. CLEAR DOWNLOAD FOLDER
    # =====================================================

    for file in DOWNLOAD_DIR.iterdir():

        try:

            if file.is_file():

                file.unlink()

        except:
            pass


    # =====================================================
    # 21. DOWNLOAD CSV
    # =====================================================

    print(
        "\nClicking Download CSV..."
    )


    driver.execute_script(
        "arguments[0].click();",
        download_button
    )


    print(
        "✓ Download clicked."
    )


    # =====================================================
    # 22. WAIT FOR CSV
    # =====================================================

    print(
        "\nWaiting for CSV download..."
    )


    end_time = time.time() + 120

    downloaded_file = None


    while time.time() < end_time:

        files = list(
            DOWNLOAD_DIR.iterdir()
        )


        csv_files = [
            f for f in files
            if f.suffix.lower() == ".csv"
        ]


        partial_files = [
            f for f in files
            if f.suffix.lower()
            in [".crdownload", ".part"]
        ]


        if csv_files and not partial_files:

            downloaded_file = max(
                csv_files,
                key=lambda f: f.stat().st_mtime
            )

            break


        time.sleep(2)


    if downloaded_file is None:

        raise Exception(
            "CSV download timeout."
        )


    print(
        "\n✓ CSV downloaded:"
    )

    print(
        downloaded_file
    )


    # =====================================================
    # 23. SAVE CSV
    # =====================================================

    OUTPUT_CSV.write_bytes(
        downloaded_file.read_bytes()
    )


    print(
        "\n✓ CSV saved:"
    )

    print(
        OUTPUT_CSV
    )


    print(
        "\nCSV size:",
        f"{OUTPUT_CSV.stat().st_size:,}",
        "bytes"
    )


    # =====================================================
    # 24. SUCCESS
    # =====================================================

    print("\n" + "=" * 80)
    print("✓✓✓ ALL-STATES EXTRACTION TEST SUCCESS ✓✓✓")
    print("=" * 80)


    print(
        "\nNow inspect the downloaded CSV."
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "We need to check whether the CSV contains"
    )

    print(
        "36 separate states OR one combined All-India total."
    )


    input(
        "\nChrome will remain open.\n"
        "Press ENTER to close... "
    )


finally:

    driver.quit()