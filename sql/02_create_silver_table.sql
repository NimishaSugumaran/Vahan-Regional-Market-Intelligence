-- ============================================================
-- 02_CREATE_SILVER_TABLE.sql
-- VAHAN Vehicle Market Intelligence Platform
-- Purpose: Create, load, and validate Silver table
-- ============================================================

USE DATABASE VAHAN_MARKET_DB;

USE SCHEMA MARKET_SCHEMA;

USE WAREHOUSE VAHAN_WH;


-- ============================================================
-- 1. CREATE SILVER TABLE
-- ============================================================

CREATE OR REPLACE TABLE SILVER_VAHAN_VEHICLE_MARKET (
    DATASET_TYPE VARCHAR,
    DIMENSION_VALUE VARCHAR,
    PERIOD VARCHAR,
    YEAR NUMBER(4,0),
    MONTH NUMBER(2,0),
    MONTH_NAME VARCHAR,
    VEHICLE_COUNT NUMBER(38,0),
    SOURCE_FILE VARCHAR,
    STATE_CODE VARCHAR,
    STATE VARCHAR,
    DATE DATE
);


-- ============================================================
-- 2. CREATE FILE FORMAT
-- ============================================================

CREATE OR REPLACE FILE FORMAT VAHAN_CSV_FORMAT
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL');


-- ============================================================
-- 3. CHECK TABLE AND STAGE
-- ============================================================

DESC TABLE SILVER_VAHAN_VEHICLE_MARKET;

LIST @SILVER_STAGE;


-- ============================================================
-- 4. LOAD CSV INTO SILVER TABLE
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
FILE_FORMAT = (FORMAT_NAME = VAHAN_CSV_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';


-- ============================================================
-- 5. OVERALL SILVER SUMMARY
-- ============================================================

SELECT
    COUNT(*) AS TOTAL_ROWS,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM SILVER_VAHAN_VEHICLE_MARKET;


-- ============================================================
-- 6. DATASET-WISE SUMMARY
-- ============================================================

SELECT
    DATASET_TYPE,
    COUNT(*) AS ROW_COUNT,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM SILVER_VAHAN_VEHICLE_MARKET
GROUP BY DATASET_TYPE
ORDER BY DATASET_TYPE;


-- ============================================================
-- 7. DATE AND STATE COVERAGE
-- ============================================================

SELECT
    MIN(DATE) AS MIN_DATE,
    MAX(DATE) AS MAX_DATE,
    COUNT(DISTINCT STATE_CODE) AS STATE_COUNT,
    COUNT(DISTINCT STATE) AS STATE_NAME_COUNT
FROM SILVER_VAHAN_VEHICLE_MARKET;


-- ============================================================
-- 8. DUPLICATE BUSINESS KEYS
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
-- 9. NULL VEHICLE COUNTS
-- ============================================================

SELECT
    COUNT(*) AS NULL_VEHICLE_COUNTS
FROM SILVER_VAHAN_VEHICLE_MARKET
WHERE VEHICLE_COUNT IS NULL;


-- ============================================================
-- 10. NEGATIVE VEHICLE COUNTS
-- ============================================================

SELECT
    COUNT(*) AS NEGATIVE_VEHICLE_COUNTS
FROM SILVER_VAHAN_VEHICLE_MARKET
WHERE VEHICLE_COUNT < 0;


-- ============================================================
-- 11. INVALID YEARS
-- ============================================================

SELECT
    COUNT(*) AS INVALID_YEARS
FROM SILVER_VAHAN_VEHICLE_MARKET
WHERE YEAR < 2016
   OR YEAR > 2026;


-- ============================================================
-- 12. INVALID MONTHS
-- ============================================================

SELECT
    COUNT(*) AS INVALID_MONTHS
FROM SILVER_VAHAN_VEHICLE_MARKET
WHERE MONTH < 1
   OR MONTH > 12;


-- ============================================================
-- 13. FINAL SILVER DATA QUALITY SUMMARY
-- ============================================================

SELECT
    'SILVER_TOTAL_ROWS' AS METRIC,
    COUNT(*) AS VALUE
FROM SILVER_VAHAN_VEHICLE_MARKET

UNION ALL

SELECT
    'SILVER_TOTAL_VEHICLES',
    SUM(VEHICLE_COUNT)
FROM SILVER_VAHAN_VEHICLE_MARKET

UNION ALL

SELECT
    'SILVER_STATE_COUNT',
    COUNT(DISTINCT STATE_CODE)
FROM SILVER_VAHAN_VEHICLE_MARKET

UNION ALL

SELECT
    'SILVER_DATASET_COUNT',
    COUNT(DISTINCT DATASET_TYPE)
FROM SILVER_VAHAN_VEHICLE_MARKET;