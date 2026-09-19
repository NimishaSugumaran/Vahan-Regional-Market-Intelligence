-- ============================================================
-- 07_SILVER_GOLD_RECONCILIATION.sql
-- VAHAN Vehicle Market Intelligence Platform
-- Purpose: Validate Silver-to-Gold totals and row counts
-- ============================================================


-- ============================================================
-- 0. DATABASE, SCHEMA AND WAREHOUSE
-- ============================================================

USE DATABASE VAHAN_MARKET_DB;
USE SCHEMA MARKET_SCHEMA;
USE WAREHOUSE VAHAN_WH;


-- ============================================================
-- 1. DATASET-WISE SILVER VS GOLD RECONCILIATION
-- ============================================================

WITH RECONCILIATION AS (

    SELECT
        'CATEGORY' AS DATASET_TYPE,

        (
            SELECT COUNT(*)
            FROM SILVER_VAHAN_VEHICLE_MARKET
            WHERE DATASET_TYPE = 'Vehicle_Category'
        ) AS SILVER_ROWS,

        (
            SELECT COUNT(*)
            FROM FACT_CATEGORY
        ) AS GOLD_ROWS,

        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM SILVER_VAHAN_VEHICLE_MARKET
            WHERE DATASET_TYPE = 'Vehicle_Category'
        ) AS SILVER_TOTAL,

        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_CATEGORY
        ) AS GOLD_TOTAL

    UNION ALL

    SELECT
        'FUEL',

        (
            SELECT COUNT(*)
            FROM SILVER_VAHAN_VEHICLE_MARKET
            WHERE DATASET_TYPE = 'Fuel'
        ),

        (
            SELECT COUNT(*)
            FROM FACT_FUEL
        ),

        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM SILVER_VAHAN_VEHICLE_MARKET
            WHERE DATASET_TYPE = 'Fuel'
        ),

        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_FUEL
        )

    UNION ALL

    SELECT
        'MANUFACTURER',

        (
            SELECT COUNT(*)
            FROM SILVER_VAHAN_VEHICLE_MARKET
            WHERE DATASET_TYPE = 'Manufacturer'
        ),

        (
            SELECT COUNT(*)
            FROM FACT_MANUFACTURER
        ),

        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM SILVER_VAHAN_VEHICLE_MARKET
            WHERE DATASET_TYPE = 'Manufacturer'
        ),

        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_MANUFACTURER
        )
)

SELECT
    DATASET_TYPE,

    SILVER_ROWS,
    GOLD_ROWS,
    SILVER_ROWS - GOLD_ROWS AS ROW_DIFFERENCE,

    SILVER_TOTAL,
    GOLD_TOTAL,
    SILVER_TOTAL - GOLD_TOTAL AS TOTAL_DIFFERENCE,

    CASE
        WHEN SILVER_ROWS = GOLD_ROWS
         AND SILVER_TOTAL = GOLD_TOTAL
        THEN 'PASS'
        ELSE 'CHECK'
    END AS RECONCILIATION_STATUS

FROM RECONCILIATION
ORDER BY DATASET_TYPE;


-- ============================================================
-- 2. OVERALL SILVER VS GOLD RECONCILIATION
-- ============================================================

WITH SILVER_TOTALS AS (
    SELECT
        COUNT(*) AS SILVER_ROWS,
        COALESCE(SUM(VEHICLE_COUNT), 0) AS SILVER_VEHICLES
    FROM SILVER_VAHAN_VEHICLE_MARKET
),

GOLD_TOTALS AS (
    SELECT
        (
            SELECT COUNT(*) FROM FACT_CATEGORY
        )
        +
        (
            SELECT COUNT(*) FROM FACT_FUEL
        )
        +
        (
            SELECT COUNT(*) FROM FACT_MANUFACTURER
        ) AS GOLD_ROWS,

        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_CATEGORY
        )
        +
        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_FUEL
        )
        +
        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_MANUFACTURER
        ) AS GOLD_VEHICLES
)

SELECT
    S.SILVER_ROWS,
    G.GOLD_ROWS,
    S.SILVER_ROWS - G.GOLD_ROWS AS ROW_DIFFERENCE,

    S.SILVER_VEHICLES,
    G.GOLD_VEHICLES,
    S.SILVER_VEHICLES - G.GOLD_VEHICLES AS TOTAL_DIFFERENCE,

    CASE
        WHEN S.SILVER_ROWS = G.GOLD_ROWS
         AND S.SILVER_VEHICLES = G.GOLD_VEHICLES
        THEN 'PASS'
        ELSE 'CHECK'
    END AS OVERALL_STATUS

FROM SILVER_TOTALS S
CROSS JOIN GOLD_TOTALS G;


-- ============================================================
-- 3. FINAL VALIDATION SUMMARY
-- ============================================================

WITH SUMMARY AS (

    SELECT
        'SILVER_TOTAL_ROWS' AS METRIC,
        COUNT(*) AS VALUE
    FROM SILVER_VAHAN_VEHICLE_MARKET

    UNION ALL

    SELECT
        'GOLD_TOTAL_ROWS',
        (
            SELECT COUNT(*) FROM FACT_CATEGORY
        )
        +
        (
            SELECT COUNT(*) FROM FACT_FUEL
        )
        +
        (
            SELECT COUNT(*) FROM FACT_MANUFACTURER
        )

    UNION ALL

    SELECT
        'SILVER_TOTAL_VEHICLES',
        COALESCE(SUM(VEHICLE_COUNT), 0)
    FROM SILVER_VAHAN_VEHICLE_MARKET

    UNION ALL

    SELECT
        'GOLD_TOTAL_VEHICLES',
        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_CATEGORY
        )
        +
        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_FUEL
        )
        +
        (
            SELECT COALESCE(SUM(VEHICLE_COUNT), 0)
            FROM FACT_MANUFACTURER
        )
)

SELECT
    METRIC,
    VALUE
FROM SUMMARY
ORDER BY
    CASE METRIC
        WHEN 'SILVER_TOTAL_ROWS' THEN 1
        WHEN 'GOLD_TOTAL_ROWS' THEN 2
        WHEN 'SILVER_TOTAL_VEHICLES' THEN 3
        WHEN 'GOLD_TOTAL_VEHICLES' THEN 4
    END;