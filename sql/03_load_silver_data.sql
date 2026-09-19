-- ============================================================
-- 03_LOAD_SILVER_DATA.sql
-- VAHAN Vehicle Market Intelligence Platform
-- Purpose: Load the latest deduplicated Silver CSV
-- ============================================================

USE DATABASE VAHAN_MARKET_DB;

USE SCHEMA MARKET_SCHEMA;

USE WAREHOUSE VAHAN_WH;


-- ============================================================
-- 1. CHECK STAGE FILES
-- ============================================================

LIST @SILVER_STAGE;


-- ============================================================
-- 2. TRUNCATE SILVER TABLE BEFORE RELOAD
-- ============================================================
-- COPY INTO is an APPEND operation, not a replace. Without this
-- truncate, every monthly run re-appends the full historical
-- dataset on top of the previous run's data, duplicating all
-- rows instead of refreshing them. This pipeline does a full
-- reprocess each run (not incremental), so Silver must be fully
-- reloaded each time to match.

TRUNCATE TABLE SILVER_VAHAN_VEHICLE_MARKET;


-- ============================================================
-- 3. LOAD LATEST DEDUPLICATED CSV
-- ============================================================

COPY INTO SILVER_VAHAN_VEHICLE_MARKET (
    DATASET_TYPE,
    DIMENSION_VALUE,
    PERIOD,
    YEAR,
    MONTH,
    MONTH_NAME,
    VEHICLE_COUNT,
    SOURCE_FILE,
    STATE_CODE,
    STATE,
    DATE
)
FROM (
    SELECT
        $1::VARCHAR,
        $2::VARCHAR,
        $3::VARCHAR,
        $4::NUMBER(4,0),
        $5::NUMBER(2,0),
        $6::VARCHAR,
        $7::NUMBER(38,0),
        $8::VARCHAR,
        $9::VARCHAR,
        $10::VARCHAR,
        $11::DATE
    FROM @SILVER_STAGE
)
FILES = ('vahan_vehicle_market_loaded.csv')
FILE_FORMAT = (
    TYPE = CSV,
    FIELD_OPTIONALLY_ENCLOSED_BY = '"',
    SKIP_HEADER = 1,
    NULL_IF = ('', 'NULL')
)
ON_ERROR = 'ABORT_STATEMENT';


-- ============================================================
-- 4. OVERALL SILVER SUMMARY
-- ============================================================

SELECT
    COUNT(*) AS TOTAL_ROWS,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM SILVER_VAHAN_VEHICLE_MARKET;


-- ============================================================
-- 5. DATASET-WISE SUMMARY
-- ============================================================

SELECT
    DATASET_TYPE,
    COUNT(*) AS ROW_COUNT,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM SILVER_VAHAN_VEHICLE_MARKET
GROUP BY DATASET_TYPE
ORDER BY DATASET_TYPE;


-- ============================================================
-- 6. STATE COVERAGE
-- ============================================================

SELECT
    COUNT(DISTINCT STATE_CODE) AS DISTINCT_STATE_CODES,
    COUNT(DISTINCT STATE) AS DISTINCT_STATES
FROM SILVER_VAHAN_VEHICLE_MARKET;


-- ============================================================
-- 7. DATE COVERAGE
-- ============================================================

SELECT
    MIN(DATE) AS MIN_DATE,
    MAX(DATE) AS MAX_DATE
FROM SILVER_VAHAN_VEHICLE_MARKET;


-- ============================================================
-- 8. NULL CHECK
-- ============================================================

SELECT
    COUNT_IF(DATASET_TYPE IS NULL) AS NULL_DATASET_TYPE,
    COUNT_IF(DIMENSION_VALUE IS NULL) AS NULL_DIMENSION_VALUE,
    COUNT_IF(PERIOD IS NULL) AS NULL_PERIOD,
    COUNT_IF(YEAR IS NULL) AS NULL_YEAR,
    COUNT_IF(MONTH IS NULL) AS NULL_MONTH,
    COUNT_IF(MONTH_NAME IS NULL) AS NULL_MONTH_NAME,
    COUNT_IF(VEHICLE_COUNT IS NULL) AS NULL_VEHICLE_COUNT,
    COUNT_IF(SOURCE_FILE IS NULL) AS NULL_SOURCE_FILE,
    COUNT_IF(STATE_CODE IS NULL) AS NULL_STATE_CODE,
    COUNT_IF(STATE IS NULL) AS NULL_STATE,
    COUNT_IF(DATE IS NULL) AS NULL_DATE
FROM SILVER_VAHAN_VEHICLE_MARKET;


-- ============================================================
-- 9. DUPLICATE BUSINESS KEY CHECK
-- ============================================================

SELECT
    DATASET_TYPE,
    STATE_CODE,
    DIMENSION_VALUE,
    PERIOD,
    DATE,
    COUNT(*) AS DUPLICATE_COUNT
FROM SILVER_VAHAN_VEHICLE_MARKET
GROUP BY
    DATASET_TYPE,
    STATE_CODE,
    DIMENSION_VALUE,
    PERIOD,
    DATE
HAVING COUNT(*) > 1
ORDER BY DUPLICATE_COUNT DESC;


-- ============================================================
-- 10. NEGATIVE VEHICLE COUNT CHECK
-- ============================================================

SELECT
    COUNT(*) AS NEGATIVE_VEHICLE_COUNT_ROWS
FROM SILVER_VAHAN_VEHICLE_MARKET
WHERE VEHICLE_COUNT < 0;


-- ============================================================
-- 11. LATEST RECORD SAMPLE
-- ============================================================

SELECT *
FROM SILVER_VAHAN_VEHICLE_MARKET
ORDER BY DATE DESC
LIMIT 20;