from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time


URL = "https://analytics.parivahan.gov.in/analytics/vahanpublicreport?lang=en"


driver = webdriver.Chrome()
wait = WebDriverWait(driver, 30)


try:

    print("=" * 80)
    print("VAHAN STATE SELECTION TEST")
    print("=" * 80)

    # =========================================================
    # 1. OPEN VAHAN PORTAL
    # =========================================================

    driver.get(URL)

    print("\n✓ VAHAN portal opened.")

    print("\nIf CAPTCHA is visible, complete it manually.")
    input("Press ENTER when page is ready... ")


    # =========================================================
    # 2. REPORT TYPE
    # =========================================================

    print("\nSelecting Report Type...")

    report_type = wait.until(
        EC.presence_of_element_located(
            (By.ID, "reportType")
        )
    )

    Select(report_type).select_by_value("0")

    print("✓ reportType selected -> 0 (Calendar Year)")

    time.sleep(2)


    # =========================================================
    # 3. Y AXIS
    # =========================================================

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


    # =========================================================
    # 4. WAIT FOR X AXIS
    # =========================================================

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

    print("✓ monthWise available in X-axis")


    # =========================================================
    # 5. SELECT MONTH WISE
    # =========================================================

    x_axis = driver.find_element(
        By.ID,
        "xAxis"
    )

    Select(x_axis).select_by_value(
        "monthWise"
    )

    print("✓ xAxis selected -> monthWise")

    time.sleep(2)


    # =========================================================
    # 6. FIND STATE SELECT
    # =========================================================

    print("\n" + "=" * 80)
    print("STATE DROPDOWN")
    print("=" * 80)

    state = wait.until(
        EC.presence_of_element_located(
            (By.ID, "stateName")
        )
    )

    print("\nTAG      :", state.tag_name)
    print("ID       :", state.get_attribute("id"))
    print("NAME     :", state.get_attribute("name"))
    print("CLASS    :", state.get_attribute("class"))
    print(
        "MULTIPLE :",
        state.get_attribute("multiple")
    )


    # =========================================================
    # 7. GET ALL STATES
    # =========================================================

    options = state.find_elements(
        By.TAG_NAME,
        "option"
    )

    print(
        "\nTotal available states:",
        len(options)
    )


    # =========================================================
    # 8. BUILD STATE CODE -> STATE NAME MAP
    # =========================================================

    state_map = {}

    for option in options:

        code = option.get_attribute("value")
        name = option.get_attribute("textContent").strip()

        if code and name:

            state_map[code] = name


    print("\nAvailable States:")

    for code, name in state_map.items():

        print(
            f"{code} -> {name}"
        )


    # =========================================================
    # 9. FIND STATE CUSTOM MULTISELECT
    # =========================================================

    print("\n" + "=" * 80)
    print("FINDING CUSTOM STATE MULTISELECT")
    print("=" * 80)

    state_container = state.find_element(
        By.XPATH,
        ".."
    )


    custom_dropdown = state_container.find_element(
        By.CSS_SELECTOR,
        "div.multiselect-dropdown"
    )

    print(
        "\n✓ Custom State dropdown found."
    )

    print(
        "Class:",
        custom_dropdown.get_attribute("class")
    )


    # =========================================================
    # 10. OPEN CUSTOM DROPDOWN
    # =========================================================

    print("\nOpening State dropdown...")

    placeholder = custom_dropdown.find_element(
        By.CSS_SELECTOR,
        "span.placeholder"
    )

    driver.execute_script(
        "arguments[0].click();",
        placeholder
    )

    time.sleep(1)

    print("✓ State dropdown opened")


    # =========================================================
    # 11. SELECT TEST STATES
    # =========================================================

    print("\n" + "=" * 80)
    print("SELECTING TEST STATES")
    print("=" * 80)


    test_states = [
        "TN",   # Tamil Nadu
        "KA",   # Karnataka
        "KL"    # Kerala
    ]


    for state_code in test_states:

        if state_code not in state_map:

            print(
                "✗ State code not found:",
                state_code
            )

            continue


        state_name = state_map[state_code]

        search_text = state_name.upper()


        # Find the state row
        state_row = custom_dropdown.find_element(
            By.CSS_SELECTOR,
            f"div[data-search-text='{search_text}']"
        )


        checkbox = state_row.find_element(
            By.CSS_SELECTOR,
            "input[type='checkbox']"
        )


        # Click using JavaScript because custom UI
        driver.execute_script(
            "arguments[0].click();",
            checkbox
        )


        print(
            "✓ Selected:",
            state_code,
            "->",
            state_name
        )


        time.sleep(0.5)


    # =========================================================
    # 12. TRIGGER STATE CHANGE
    # =========================================================

    print("\nTriggering State change event...")

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


    # =========================================================
    # 13. VERIFY SELECTED STATES
    # =========================================================

    print("\n" + "=" * 80)
    print("VERIFYING SELECTED STATES")
    print("=" * 80)


    # Re-find state element
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


    selected_values = []


    for option in selected:

        code = option.get_attribute("value")

        name = option.get_attribute(
            "textContent"
        ).strip()

        selected_values.append(code)

        print(
            "SELECTED:",
            code,
            "|",
            name
        )


    # =========================================================
    # 14. FINAL VERIFICATION
    # =========================================================

    print("\n" + "=" * 80)
    print("FINAL VERIFICATION")
    print("=" * 80)


    print(
        "\nExpected:",
        test_states
    )

    print(
        "Actual  :",
        selected_values
    )


    if set(selected_values) == set(test_states):

        print(
            "\n✓✓✓ STATE SELECTION TEST PASSED ✓✓✓"
        )

    else:

        print(
            "\n✗ STATE SELECTION TEST FAILED"
        )


    # =========================================================
    # 15. SHOW CUSTOM DROPDOWN
    # =========================================================

    print("\n" + "=" * 80)
    print("CUSTOM DROPDOWN STATUS")
    print("=" * 80)


    print(
        "\nDropdown text after selection:"
    )

    print(
        custom_dropdown.text
    )


    # =========================================================
    # 16. FINAL SUMMARY
    # =========================================================

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)


    print(
        "\nPortal loaded        : YES"
    )

    print(
        "Report Type          : Calendar Year"
    )

    print(
        "Y Axis               : Vehicle Category"
    )

    print(
        "X Axis               : Month Wise"
    )

    print(
        "State control        : stateName"
    )

    print(
        "Available states     :",
        len(state_map)
    )

    print(
        "Selected test states :",
        len(selected_values)
    )


    print(
        "\nTest states:"
    )

    for code in test_states:

        print(
            code,
            "->",
            state_map.get(code, "NOT FOUND")
        )


    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


    input(
        "\nChrome will remain open.\n"
        "Press ENTER to close..."
    )


finally:

    driver.quit()