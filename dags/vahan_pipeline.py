import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/src")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook


# ============================================================
# Configuration
# ============================================================

SNOWFLAKE_CONN_ID = "snowflake_default"

SNOWFLAKE_DATABASE = "VAHAN_MARKET_DB"
SNOWFLAKE_SCHEMA = "MARKET_SCHEMA"
SNOWFLAKE_ROLE = "ACCOUNTADMIN"
SNOWFLAKE_WAREHOUSE = "VAHAN_WH"

SQL_DIR = "/opt/airflow/sql"

LOADED_CSV_PATH = (
    "/opt/airflow/data/loaded/"
    "vahan_vehicle_market_loaded.csv"
)


# ============================================================
# Existing Local Pipeline Tasks
# ============================================================

def extract_vahan():
    from extraction.extract_all_vahan import extract_all_vahan_data
    extract_all_vahan_data()


def validate_unified():
    from validation.validate_unified_vahan import validate_unified_vahan_data
    validate_unified_vahan_data()


def transform_to_silver():
    from transformation.transform_vahan import transform_vahan_data
    transform_vahan_data()


def validate_silver():
    from validation.validate_silver import validate_silver_data
    validate_silver_data()


def deduplicate_silver():
    from transformation.deduplicate_unified_vahan import (
        deduplicate_silver_data
    )
    deduplicate_silver_data()


def load_vahan():
    from loading.load_vahan import load_vahan_data
    load_vahan_data()


# ============================================================
# Snowflake Helper Functions
# ============================================================

def get_snowflake_connection():
    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID
    )

    return hook.get_conn()


def set_snowflake_context(cursor):
    """
    Explicitly set Snowflake execution context.
    """

    cursor.execute(
        f"USE ROLE {SNOWFLAKE_ROLE}"
    )

    cursor.execute(
        f"USE WAREHOUSE {SNOWFLAKE_WAREHOUSE}"
    )

    cursor.execute(
        f"USE DATABASE {SNOWFLAKE_DATABASE}"
    )

    cursor.execute(
        f"USE SCHEMA {SNOWFLAKE_SCHEMA}"
    )

    print(
        "Snowflake context set successfully: "
        f"{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}"
    )


def execute_sql_file(file_name):
    """
    Execute a SQL file from the flat SQL directory.
    """

    file_path = os.path.join(
        SQL_DIR,
        file_name
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"SQL file not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8-sig"
    ) as file:
        sql_text = file.read()

    conn = get_snowflake_connection()
    cursor = None

    try:
        cursor = conn.cursor()

        set_snowflake_context(cursor)

        print(
            f"Executing SQL file: {file_name}"
        )

        statements = [
            statement.strip()
            for statement in sql_text.split(";")
            if statement.strip()
        ]

        statements_executed = 0

        for index, statement in enumerate(
            statements,
            start=1
        ):
            print(
                f"Executing statement "
                f"{index}/{len(statements)}"
            )

            cursor.execute(statement)

            statements_executed += 1

        conn.commit()

        print(
            f"Completed SQL file: {file_name} | "
            f"Statements executed: {statements_executed}"
        )

    finally:
        if cursor is not None:
            cursor.close()

        conn.close()


# ============================================================
# Snowflake Tasks
# ============================================================

def test_snowflake_connection():
    conn = get_snowflake_connection()
    cursor = None

    try:
        cursor = conn.cursor()

        set_snowflake_context(cursor)

        cursor.execute(
            """
            SELECT
                CURRENT_USER(),
                CURRENT_ACCOUNT(),
                CURRENT_DATABASE(),
                CURRENT_SCHEMA(),
                CURRENT_WAREHOUSE(),
                CURRENT_ROLE()
            """
        )

        result = cursor.fetchone()

        print("Snowflake connection successful")
        print(f"Current User: {result[0]}")
        print(f"Current Account: {result[1]}")
        print(f"Current Database: {result[2]}")
        print(f"Current Schema: {result[3]}")
        print(f"Current Warehouse: {result[4]}")
        print(f"Current Role: {result[5]}")

    finally:
        if cursor is not None:
            cursor.close()

        conn.close()


def setup_snowflake():
    execute_sql_file(
        "01_snowflake_setup.sql"
    )


def upload_to_snowflake_stage():
    if not os.path.exists(LOADED_CSV_PATH):
        raise FileNotFoundError(
            f"Loaded CSV not found: {LOADED_CSV_PATH}"
        )

    conn = get_snowflake_connection()
    cursor = None

    try:
        cursor = conn.cursor()

        set_snowflake_context(cursor)

        stage_name = (
            f"{SNOWFLAKE_DATABASE}."
            f"{SNOWFLAKE_SCHEMA}."
            "SILVER_STAGE"
        )

        put_sql = f"""
            PUT 'file://{LOADED_CSV_PATH}'
            @{stage_name}
            AUTO_COMPRESS=FALSE
            OVERWRITE=TRUE
        """

        print(
            "Uploading loaded CSV to Snowflake stage..."
        )

        print(
            f"Target stage: @{stage_name}"
        )

        cursor.execute(put_sql)

        print(
            "Snowflake stage upload completed successfully"
        )

    finally:
        if cursor is not None:
            cursor.close()

        conn.close()


def create_silver_table():
    execute_sql_file(
        "02_create_silver_table.sql"
    )


def load_snowflake_silver():
    execute_sql_file(
        "03_load_silver_data.sql"
    )


def build_gold_model():
    execute_sql_file(
        "04_gold_model.sql"
    )


def build_analytics_views():
    execute_sql_file(
        "05_analytics_views.sql"
    )


def run_reconciliation():
    execute_sql_file(
        "07_silver_gold_reconciliation.sql"
    )


def write_validation_summary():
    conn = get_snowflake_connection()
    cursor = None

    try:
        cursor = conn.cursor()

        set_snowflake_context(cursor)

        cursor.execute("DELETE FROM PIPELINE_VALIDATION_SUMMARY")

        cursor.execute(
            """
            INSERT INTO PIPELINE_VALIDATION_SUMMARY
                (METRIC_NAME, METRIC_VALUE, STATUS, VALIDATION_DATE)

            SELECT 'Silver Records Processed',
                   TO_VARCHAR(COUNT(*)),
                   'PASS',
                   CURRENT_TIMESTAMP()
            FROM SILVER_VAHAN_VEHICLE_MARKET

            UNION ALL

            SELECT 'Silver Vehicle-Count Total',
                   TO_VARCHAR(SUM(VEHICLE_COUNT)),
                   'PASS',
                   CURRENT_TIMESTAMP()
            FROM SILVER_VAHAN_VEHICLE_MARKET

            UNION ALL

            SELECT 'Data Quality Errors',
                   TO_VARCHAR(
                       COUNT_IF(VEHICLE_COUNT IS NULL)
                       + COUNT_IF(VEHICLE_COUNT < 0)
                       + COUNT_IF(DATE IS NULL)
                   ),
                   CASE
                       WHEN COUNT_IF(VEHICLE_COUNT IS NULL)
                            + COUNT_IF(VEHICLE_COUNT < 0)
                            + COUNT_IF(DATE IS NULL) = 0
                       THEN 'PASS'
                       ELSE 'CHECK'
                   END,
                   CURRENT_TIMESTAMP()
            FROM SILVER_VAHAN_VEHICLE_MARKET

            UNION ALL

            SELECT 'Reconciliation Status',
                   CASE
                       WHEN (SELECT COUNT(*) FROM SILVER_VAHAN_VEHICLE_MARKET)
                            = (
                                (SELECT COUNT(*) FROM FACT_CATEGORY)
                                + (SELECT COUNT(*) FROM FACT_FUEL)
                                + (SELECT COUNT(*) FROM FACT_MANUFACTURER)
                              )
                       THEN 'Silver-Gold row counts match'
                       ELSE 'Row count mismatch - review'
                   END,
                   CASE
                       WHEN (SELECT COUNT(*) FROM SILVER_VAHAN_VEHICLE_MARKET)
                            = (
                                (SELECT COUNT(*) FROM FACT_CATEGORY)
                                + (SELECT COUNT(*) FROM FACT_FUEL)
                                + (SELECT COUNT(*) FROM FACT_MANUFACTURER)
                              )
                       THEN 'PASS'
                       ELSE 'FAIL'
                   END,
                   CURRENT_TIMESTAMP()
            """
        )

        conn.commit()

        print(
            "Validation summary written successfully"
        )

    finally:
        if cursor is not None:
            cursor.close()

        conn.close()


# ============================================================
# Failure Callback (logs to Airflow task log; extend to email/
# Slack later if needed)
# ============================================================

def task_failure_alert(context):
    task_instance = context.get("task_instance")
    dag_run = context.get("dag_run")

    print(
        "PIPELINE TASK FAILED | "
        f"DAG: {dag_run.dag_id if dag_run else 'unknown'} | "
        f"Task: {task_instance.task_id if task_instance else 'unknown'} | "
        f"Execution date: {context.get('execution_date')}"
    )


# ============================================================
# DAG Definition
# ============================================================

default_args = {
    "owner": "vahan_project",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": task_failure_alert,
}


with DAG(
    dag_id="vahan_vehicle_market_pipeline",

    default_args=default_args,

    description=(
        "End-to-end VAHAN Regional Vehicle Market "
        "Data Engineering Pipeline"
    ),

    start_date=datetime(2026, 1, 1),

    # Manual-triggered: source extraction requires a manual
    # CAPTCHA checkpoint, so production scheduling is
    # intentionally manual-triggered rather than unattended.
    schedule=None,

    catchup=False,

    tags=[
        "vahan",
        "data-engineering",
        "india",
        "snowflake",
    ],
) as dag:

    # ========================================================
    # Local Data Pipeline
    # ========================================================

    extract_task = PythonOperator(
        task_id="extract_vahan_data",
        python_callable=extract_vahan,
        # Selenium extraction over 724 reports can run long;
        # without this, a hung browser session blocks the DAG
        # indefinitely instead of failing and retrying.
        execution_timeout=timedelta(hours=3),
    )

    validate_unified_task = PythonOperator(
        task_id="validate_unified_data",
        python_callable=validate_unified,
    )

    silver_transform_task = PythonOperator(
        task_id="transform_to_silver",
        python_callable=transform_to_silver,
    )

    silver_validation_task = PythonOperator(
        task_id="validate_silver_data",
        python_callable=validate_silver,
    )

    deduplication_task = PythonOperator(
        task_id="deduplicate_silver_data",
        python_callable=deduplicate_silver,
    )

    load_task = PythonOperator(
        task_id="load_vahan_data",
        python_callable=load_vahan,
    )

    # ========================================================
    # Snowflake Pipeline
    # ========================================================

    snowflake_test_task = PythonOperator(
        task_id="test_snowflake_connection",
        python_callable=test_snowflake_connection,
    )

    setup_snowflake_task = PythonOperator(
        task_id="setup_snowflake",
        python_callable=setup_snowflake,
    )

    upload_stage_task = PythonOperator(
        task_id="upload_to_snowflake_stage",
        python_callable=upload_to_snowflake_stage,
    )

    create_silver_task = PythonOperator(
        task_id="create_snowflake_silver_table",
        python_callable=create_silver_table,
    )

    load_silver_task = PythonOperator(
        task_id="load_snowflake_silver",
        python_callable=load_snowflake_silver,
    )

    gold_model_task = PythonOperator(
        task_id="build_gold_model",
        python_callable=build_gold_model,
    )

    analytics_views_task = PythonOperator(
        task_id="build_analytics_views",
        python_callable=build_analytics_views,
    )

    reconciliation_task = PythonOperator(
        task_id="run_reconciliation",
        python_callable=run_reconciliation,
    )

    validation_summary_task = PythonOperator(
        task_id="write_validation_summary",
        python_callable=write_validation_summary,
    )

    # ========================================================
    # Dependency Chain
    # ========================================================

    (
        extract_task
        >> validate_unified_task
        >> silver_transform_task
        >> silver_validation_task
        >> deduplication_task
        >> load_task
        >> snowflake_test_task
        >> setup_snowflake_task
        >> upload_stage_task
        >> create_silver_task
        >> load_silver_task
        >> gold_model_task
        >> analytics_views_task
        >> reconciliation_task
        >> validation_summary_task
    )