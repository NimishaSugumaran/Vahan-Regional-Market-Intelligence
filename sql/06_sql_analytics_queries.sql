-- ============================================================
-- 06_SQL_ANALYTICS_QUERIES.sql
-- VAHAN Regional Vehicle Market Intelligence Platform
-- 35 Business Analytics Queries
-- ============================================================


-- ============================================================
-- 0. DATABASE, SCHEMA AND WAREHOUSE
-- ============================================================

USE DATABASE VAHAN_MARKET_DB;
USE SCHEMA MARKET_SCHEMA;
USE WAREHOUSE VAHAN_WH;


-- ============================================================
-- 01. TOP VEHICLE CATEGORIES
-- ============================================================

SELECT
    CATEGORY_NAME,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM FACT_CATEGORY
GROUP BY CATEGORY_NAME
ORDER BY TOTAL_VEHICLES DESC
LIMIT 10;


-- ============================================================
-- 02. TOP FUEL TYPES
-- ============================================================

SELECT
    FUEL_NAME,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM FACT_FUEL
GROUP BY FUEL_NAME
ORDER BY TOTAL_VEHICLES DESC
LIMIT 10;


-- ============================================================
-- 03. TOP MANUFACTURERS
-- ============================================================

SELECT
    MANUFACTURER_NAME,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM FACT_MANUFACTURER
GROUP BY MANUFACTURER_NAME
ORDER BY TOTAL_VEHICLES DESC
LIMIT 10;


-- ============================================================
-- 04. CATEGORY YEAR-WISE TREND
-- ============================================================

SELECT
    YEAR,
    CATEGORY_NAME,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM FACT_CATEGORY
GROUP BY YEAR, CATEGORY_NAME
ORDER BY YEAR, TOTAL_VEHICLES DESC;


-- ============================================================
-- 05. FUEL YEAR-WISE TREND
-- ============================================================

SELECT
    YEAR,
    FUEL_NAME,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM FACT_FUEL
GROUP BY YEAR, FUEL_NAME
ORDER BY YEAR, TOTAL_VEHICLES DESC;


-- ============================================================
-- 06. MANUFACTURER YEAR-WISE TREND
-- ============================================================

SELECT
    YEAR,
    MANUFACTURER_NAME,
    SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
FROM FACT_MANUFACTURER
GROUP BY YEAR, MANUFACTURER_NAME
ORDER BY YEAR, TOTAL_VEHICLES DESC;


-- ============================================================
-- 07. MONTH-WISE REGISTRATION TREND
-- NOTE:
-- This combines all three official report datasets.
-- It is descriptive, not a unique vehicle-market total.
-- ============================================================

SELECT
    DATE,
    YEAR,
    MONTH,
    MONTH_NAME,
    SUM(VEHICLE_COUNT) AS REPORTED_VEHICLE_COUNT
FROM SILVER_VAHAN_VEHICLE_MARKET
GROUP BY
    DATE,
    YEAR,
    MONTH,
    MONTH_NAME
ORDER BY DATE;


-- ============================================================
-- 08. TOP 10 CATEGORIES BY YEAR
-- ============================================================

WITH CATEGORY_YEARLY AS (
    SELECT
        YEAR,
        CATEGORY_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_CATEGORY
    GROUP BY YEAR, CATEGORY_NAME
),

RANKED AS (
    SELECT
        YEAR,
        CATEGORY_NAME,
        TOTAL_VEHICLES,
        ROW_NUMBER() OVER (
            PARTITION BY YEAR
            ORDER BY TOTAL_VEHICLES DESC, CATEGORY_NAME
        ) AS RN
    FROM CATEGORY_YEARLY
)

SELECT
    YEAR,
    CATEGORY_NAME,
    TOTAL_VEHICLES
FROM RANKED
WHERE RN <= 10
ORDER BY YEAR, TOTAL_VEHICLES DESC;


-- ============================================================
-- 09. TOP 10 FUEL TYPES BY YEAR
-- ============================================================

WITH FUEL_YEARLY AS (
    SELECT
        YEAR,
        FUEL_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_FUEL
    GROUP BY YEAR, FUEL_NAME
),

RANKED AS (
    SELECT
        YEAR,
        FUEL_NAME,
        TOTAL_VEHICLES,
        ROW_NUMBER() OVER (
            PARTITION BY YEAR
            ORDER BY TOTAL_VEHICLES DESC, FUEL_NAME
        ) AS RN
    FROM FUEL_YEARLY
)

SELECT
    YEAR,
    FUEL_NAME,
    TOTAL_VEHICLES
FROM RANKED
WHERE RN <= 10
ORDER BY YEAR, TOTAL_VEHICLES DESC;


-- ============================================================
-- 10. TOP 10 MANUFACTURERS BY YEAR
-- ============================================================

WITH MANUFACTURER_YEARLY AS (
    SELECT
        YEAR,
        MANUFACTURER_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_MANUFACTURER
    GROUP BY YEAR, MANUFACTURER_NAME
),

RANKED AS (
    SELECT
        YEAR,
        MANUFACTURER_NAME,
        TOTAL_VEHICLES,
        ROW_NUMBER() OVER (
            PARTITION BY YEAR
            ORDER BY TOTAL_VEHICLES DESC, MANUFACTURER_NAME
        ) AS RN
    FROM MANUFACTURER_YEARLY
)

SELECT
    YEAR,
    MANUFACTURER_NAME,
    TOTAL_VEHICLES
FROM RANKED
WHERE RN <= 10
ORDER BY YEAR, TOTAL_VEHICLES DESC;


-- ============================================================
-- 11. MANUFACTURER MARKET SHARE
-- ============================================================

SELECT
    MANUFACTURER_NAME,
    TOTAL_VEHICLES,
    ROUND(
        TOTAL_VEHICLES * 100.0
        / NULLIF(SUM(TOTAL_VEHICLES) OVER (), 0),
        2
    ) AS MARKET_SHARE_PERCENT
FROM VW_MANUFACTURER_TOTALS
ORDER BY TOTAL_VEHICLES DESC
LIMIT 20;


-- ============================================================
-- 12. FUEL MARKET SHARE
-- ============================================================

SELECT
    FUEL_NAME,
    TOTAL_VEHICLES,
    ROUND(
        TOTAL_VEHICLES * 100.0
        / NULLIF(SUM(TOTAL_VEHICLES) OVER (), 0),
        2
    ) AS MARKET_SHARE_PERCENT
FROM VW_FUEL_TOTALS
ORDER BY TOTAL_VEHICLES DESC;


-- ============================================================
-- 13. CATEGORY MARKET SHARE
-- ============================================================

SELECT
    CATEGORY_NAME,
    TOTAL_VEHICLES,
    ROUND(
        TOTAL_VEHICLES * 100.0
        / NULLIF(SUM(TOTAL_VEHICLES) OVER (), 0),
        2
    ) AS MARKET_SHARE_PERCENT
FROM VW_CATEGORY_TOTALS
ORDER BY TOTAL_VEHICLES DESC;


-- ============================================================
-- 14. YEAR-OVER-YEAR CATEGORY GROWTH
-- ============================================================

WITH CATEGORY_YEARLY AS (
    SELECT
        YEAR,
        CATEGORY_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_CATEGORY
    GROUP BY YEAR, CATEGORY_NAME
),

CATEGORY_GROWTH AS (
    SELECT
        YEAR,
        CATEGORY_NAME,
        TOTAL_VEHICLES,
        LAG(TOTAL_VEHICLES) OVER (
            PARTITION BY CATEGORY_NAME
            ORDER BY YEAR
        ) AS PREVIOUS_YEAR_VEHICLES
    FROM CATEGORY_YEARLY
)

SELECT
    YEAR,
    CATEGORY_NAME,
    TOTAL_VEHICLES,
    PREVIOUS_YEAR_VEHICLES,
    TOTAL_VEHICLES - PREVIOUS_YEAR_VEHICLES AS YOY_CHANGE,
    ROUND(
        (TOTAL_VEHICLES - PREVIOUS_YEAR_VEHICLES) * 100.0
        / NULLIF(PREVIOUS_YEAR_VEHICLES, 0),
        2
    ) AS YOY_GROWTH_PERCENT
FROM CATEGORY_GROWTH
ORDER BY CATEGORY_NAME, YEAR;


-- ============================================================
-- 15. YEAR-OVER-YEAR FUEL GROWTH
-- ============================================================

WITH FUEL_YEARLY AS (
    SELECT
        YEAR,
        FUEL_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_FUEL
    GROUP BY YEAR, FUEL_NAME
),

FUEL_GROWTH AS (
    SELECT
        YEAR,
        FUEL_NAME,
        TOTAL_VEHICLES,
        LAG(TOTAL_VEHICLES) OVER (
            PARTITION BY FUEL_NAME
            ORDER BY YEAR
        ) AS PREVIOUS_YEAR_VEHICLES
    FROM FUEL_YEARLY
)

SELECT
    YEAR,
    FUEL_NAME,
    TOTAL_VEHICLES,
    PREVIOUS_YEAR_VEHICLES,
    TOTAL_VEHICLES - PREVIOUS_YEAR_VEHICLES AS YOY_CHANGE,
    ROUND(
        (TOTAL_VEHICLES - PREVIOUS_YEAR_VEHICLES) * 100.0
        / NULLIF(PREVIOUS_YEAR_VEHICLES, 0),
        2
    ) AS YOY_GROWTH_PERCENT
FROM FUEL_GROWTH
ORDER BY FUEL_NAME, YEAR;


-- ============================================================
-- 16. YEAR-OVER-YEAR MANUFACTURER GROWTH
-- ============================================================

WITH MANUFACTURER_YEARLY AS (
    SELECT
        YEAR,
        MANUFACTURER_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_MANUFACTURER
    GROUP BY YEAR, MANUFACTURER_NAME
),

MANUFACTURER_GROWTH AS (
    SELECT
        YEAR,
        MANUFACTURER_NAME,
        TOTAL_VEHICLES,
        LAG(TOTAL_VEHICLES) OVER (
            PARTITION BY MANUFACTURER_NAME
            ORDER BY YEAR
        ) AS PREVIOUS_YEAR_VEHICLES
    FROM MANUFACTURER_YEARLY
)

SELECT
    YEAR,
    MANUFACTURER_NAME,
    TOTAL_VEHICLES,
    PREVIOUS_YEAR_VEHICLES,
    TOTAL_VEHICLES - PREVIOUS_YEAR_VEHICLES AS YOY_CHANGE,
    ROUND(
        (TOTAL_VEHICLES - PREVIOUS_YEAR_VEHICLES) * 100.0
        / NULLIF(PREVIOUS_YEAR_VEHICLES, 0),
        2
    ) AS YOY_GROWTH_PERCENT
FROM MANUFACTURER_GROWTH
ORDER BY MANUFACTURER_NAME, YEAR;


-- ============================================================
-- 17. PEAK REGISTRATION MONTH
-- ============================================================

WITH MONTHLY_TOTALS AS (
    SELECT
        DATE,
        YEAR,
        MONTH,
        MONTH_NAME,
        SUM(VEHICLE_COUNT) AS REPORTED_VEHICLE_COUNT
    FROM SILVER_VAHAN_VEHICLE_MARKET
    GROUP BY DATE, YEAR, MONTH, MONTH_NAME
)

SELECT
    YEAR,
    MONTH,
    MONTH_NAME,
    DATE,
    REPORTED_VEHICLE_COUNT
FROM MONTHLY_TOTALS
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY YEAR
    ORDER BY REPORTED_VEHICLE_COUNT DESC, DATE
) = 1
ORDER BY YEAR;


-- ============================================================
-- 18. LOWEST REGISTRATION MONTH
-- ============================================================

WITH MONTHLY_TOTALS AS (
    SELECT
        DATE,
        YEAR,
        MONTH,
        MONTH_NAME,
        SUM(VEHICLE_COUNT) AS REPORTED_VEHICLE_COUNT
    FROM SILVER_VAHAN_VEHICLE_MARKET
    GROUP BY DATE, YEAR, MONTH, MONTH_NAME
)

SELECT
    YEAR,
    MONTH,
    MONTH_NAME,
    DATE,
    REPORTED_VEHICLE_COUNT
FROM MONTHLY_TOTALS
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY YEAR
    ORDER BY REPORTED_VEHICLE_COUNT ASC, DATE
) = 1
ORDER BY YEAR;


-- ============================================================
-- 19. CATEGORY-FUEL REPORTED TREND COMPARISON
-- NOTE:
-- Category and Fuel are separate VAHAN report grains.
-- This is a descriptive comparison, not a unique market total.
-- ============================================================

WITH CATEGORY_YEARLY AS (
    SELECT
        YEAR,
        SUM(VEHICLE_COUNT) AS CATEGORY_REPORTED_COUNT
    FROM FACT_CATEGORY
    GROUP BY YEAR
),

FUEL_YEARLY AS (
    SELECT
        YEAR,
        SUM(VEHICLE_COUNT) AS FUEL_REPORTED_COUNT
    FROM FACT_FUEL
    GROUP BY YEAR
)

SELECT
    C.YEAR,
    C.CATEGORY_REPORTED_COUNT,
    F.FUEL_REPORTED_COUNT,

    C.CATEGORY_REPORTED_COUNT
        - F.FUEL_REPORTED_COUNT AS REPORTED_COUNT_DIFFERENCE,

    ROUND(
        C.CATEGORY_REPORTED_COUNT * 100.0
        / NULLIF(F.FUEL_REPORTED_COUNT, 0),
        2
    ) AS CATEGORY_TO_FUEL_RATIO_PERCENT

FROM CATEGORY_YEARLY C
JOIN FUEL_YEARLY F
    ON C.YEAR = F.YEAR
ORDER BY C.YEAR;


-- ============================================================
-- 20. MANUFACTURER CONCENTRATION
-- ============================================================

WITH MANUFACTURER_RANKED AS (
    SELECT
        MANUFACTURER_NAME,
        TOTAL_VEHICLES,
        ROW_NUMBER() OVER (
            ORDER BY TOTAL_VEHICLES DESC, MANUFACTURER_NAME
        ) AS MANUFACTURER_RANK
    FROM VW_MANUFACTURER_TOTALS
)

SELECT
    SUM(
        CASE
            WHEN MANUFACTURER_RANK <= 5
            THEN TOTAL_VEHICLES
            ELSE 0
        END
    ) AS TOP_5_VEHICLES,

    SUM(TOTAL_VEHICLES) AS TOTAL_REPORTED_MANUFACTURER_VEHICLES,

    ROUND(
        SUM(
            CASE
                WHEN MANUFACTURER_RANK <= 5
                THEN TOTAL_VEHICLES
                ELSE 0
            END
        ) * 100.0
        / NULLIF(SUM(TOTAL_VEHICLES), 0),
        2
    ) AS TOP_5_CONCENTRATION_PERCENT

FROM MANUFACTURER_RANKED;


-- ============================================================
-- 21. CATEGORY CONCENTRATION
-- ============================================================

WITH CATEGORY_RANKED AS (
    SELECT
        CATEGORY_NAME,
        TOTAL_VEHICLES,
        ROW_NUMBER() OVER (
            ORDER BY TOTAL_VEHICLES DESC, CATEGORY_NAME
        ) AS CATEGORY_RANK
    FROM VW_CATEGORY_TOTALS
)

SELECT
    SUM(
        CASE
            WHEN CATEGORY_RANK <= 3
            THEN TOTAL_VEHICLES
            ELSE 0
        END
    ) AS TOP_3_CATEGORIES_VEHICLES,

    SUM(TOTAL_VEHICLES) AS TOTAL_REPORTED_CATEGORY_VEHICLES,

    ROUND(
        SUM(
            CASE
                WHEN CATEGORY_RANK <= 3
                THEN TOTAL_VEHICLES
                ELSE 0
            END
        ) * 100.0
        / NULLIF(SUM(TOTAL_VEHICLES), 0),
        2
    ) AS TOP_3_CONCENTRATION_PERCENT

FROM CATEGORY_RANKED;


-- ============================================================
-- 22. FUEL CONCENTRATION
-- ============================================================

WITH FUEL_RANKED AS (
    SELECT
        FUEL_NAME,
        TOTAL_VEHICLES,
        ROW_NUMBER() OVER (
            ORDER BY TOTAL_VEHICLES DESC, FUEL_NAME
        ) AS FUEL_RANK
    FROM VW_FUEL_TOTALS
)

SELECT
    SUM(
        CASE
            WHEN FUEL_RANK <= 3
            THEN TOTAL_VEHICLES
            ELSE 0
        END
    ) AS TOP_3_FUEL_VEHICLES,

    SUM(TOTAL_VEHICLES) AS TOTAL_REPORTED_FUEL_VEHICLES,

    ROUND(
        SUM(
            CASE
                WHEN FUEL_RANK <= 3
                THEN TOTAL_VEHICLES
                ELSE 0
            END
        ) * 100.0
        / NULLIF(SUM(TOTAL_VEHICLES), 0),
        2
    ) AS TOP_3_CONCENTRATION_PERCENT

FROM FUEL_RANKED;


-- ============================================================
-- 23. DATASET TYPE DISTRIBUTION
-- ============================================================

SELECT
    DATASET_TYPE,
    COUNT(*) AS ROW_COUNT,
    SUM(VEHICLE_COUNT) AS REPORTED_VEHICLES,

    ROUND(
        SUM(VEHICLE_COUNT) * 100.0
        / NULLIF(
            SUM(SUM(VEHICLE_COUNT)) OVER (),
            0
        ),
        2
    ) AS SHARE_OF_REPORTED_RECORDS_PERCENT

FROM SILVER_VAHAN_VEHICLE_MARKET
GROUP BY DATASET_TYPE
ORDER BY REPORTED_VEHICLES DESC;


-- ============================================================
-- 24. ANNUAL REPORTED VEHICLE COUNT
-- ============================================================

SELECT
    YEAR,
    SUM(VEHICLE_COUNT) AS REPORTED_VEHICLE_COUNT
FROM SILVER_VAHAN_VEHICLE_MARKET
GROUP BY YEAR
ORDER BY YEAR;


-- ============================================================
-- 25. MONTHLY REPORTED VEHICLE COUNT WITH RANK
-- ============================================================

WITH MONTHLY_TOTALS AS (
    SELECT
        DATE,
        YEAR,
        MONTH,
        MONTH_NAME,
        SUM(VEHICLE_COUNT) AS REPORTED_VEHICLE_COUNT
    FROM SILVER_VAHAN_VEHICLE_MARKET
    GROUP BY DATE, YEAR, MONTH, MONTH_NAME
)

SELECT
    YEAR,
    MONTH,
    MONTH_NAME,
    DATE,
    REPORTED_VEHICLE_COUNT,

    RANK() OVER (
        PARTITION BY YEAR
        ORDER BY REPORTED_VEHICLE_COUNT DESC
    ) AS MONTH_RANK

FROM MONTHLY_TOTALS
ORDER BY YEAR, MONTH_RANK;


-- ============================================================
-- 26. TOP MANUFACTURER FOR EACH YEAR
-- ============================================================

WITH MANUFACTURER_YEARLY AS (
    SELECT
        YEAR,
        MANUFACTURER_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_MANUFACTURER
    GROUP BY YEAR, MANUFACTURER_NAME
)

SELECT
    YEAR,
    MANUFACTURER_NAME,
    TOTAL_VEHICLES
FROM MANUFACTURER_YEARLY
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY YEAR
    ORDER BY TOTAL_VEHICLES DESC, MANUFACTURER_NAME
) = 1
ORDER BY YEAR;


-- ============================================================
-- 27. TOP CATEGORY FOR EACH YEAR
-- ============================================================

WITH CATEGORY_YEARLY AS (
    SELECT
        YEAR,
        CATEGORY_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_CATEGORY
    GROUP BY YEAR, CATEGORY_NAME
)

SELECT
    YEAR,
    CATEGORY_NAME,
    TOTAL_VEHICLES
FROM CATEGORY_YEARLY
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY YEAR
    ORDER BY TOTAL_VEHICLES DESC, CATEGORY_NAME
) = 1
ORDER BY YEAR;


-- ============================================================
-- 28. TOP FUEL FOR EACH YEAR
-- ============================================================

WITH FUEL_YEARLY AS (
    SELECT
        YEAR,
        FUEL_NAME,
        SUM(VEHICLE_COUNT) AS TOTAL_VEHICLES
    FROM FACT_FUEL
    GROUP BY YEAR, FUEL_NAME
)

SELECT
    YEAR,
    FUEL_NAME,
    TOTAL_VEHICLES
FROM FUEL_YEARLY
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY YEAR
    ORDER BY TOTAL_VEHICLES DESC, FUEL_NAME
) = 1
ORDER BY YEAR;


-- ============================================================
-- 29. ZERO COUNT RECORD ANALYSIS
-- ============================================================

-- ============================================================
-- QUERY 29: ZERO VEHICLE COUNT ANALYSIS
-- ============================================================

SELECT
    DATASET_TYPE,

    COUNT_IF(VEHICLE_COUNT = 0) AS ZERO_COUNT_ROWS,

    COUNT(*) AS TOTAL_ROWS,

    ROUND(
        COUNT_IF(VEHICLE_COUNT = 0) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    ) AS ZERO_COUNT_PERCENT_WITHIN_DATASET

FROM SILVER_VAHAN_VEHICLE_MARKET

GROUP BY DATASET_TYPE

ORDER BY ZERO_COUNT_ROWS DESC;

-- ============================================================
-- 30. DATA QUALITY SUMMARY
-- ============================================================

WITH DUPLICATE_KEYS AS (
    SELECT
        DATASET_TYPE,
        STATE_CODE,
        DIMENSION_VALUE,
        PERIOD,
        DATE
    FROM SILVER_VAHAN_VEHICLE_MARKET
    GROUP BY
        DATASET_TYPE,
        STATE_CODE,
        DIMENSION_VALUE,
        PERIOD,
        DATE
    HAVING COUNT(*) > 1
)

SELECT
    COUNT(*) AS TOTAL_ROWS,

    COUNT_IF(VEHICLE_COUNT IS NULL)
        AS NULL_VEHICLE_COUNTS,

    COUNT_IF(VEHICLE_COUNT < 0)
        AS NEGATIVE_VEHICLE_COUNTS,

    COUNT_IF(YEAR < 2016 OR YEAR > 2026)
        AS INVALID_YEARS,

    COUNT_IF(MONTH < 1 OR MONTH > 12)
        AS INVALID_MONTHS,

    COUNT_IF(DATE IS NULL)
        AS NULL_DATES,

    COUNT(DISTINCT DATASET_TYPE)
        AS DATASET_TYPES,

    (
        SELECT COUNT(*)
        FROM DUPLICATE_KEYS
    ) AS DUPLICATE_BUSINESS_KEY_GROUPS

FROM SILVER_VAHAN_VEHICLE_MARKET;


-- ============================================================
-- 31. STATE-WISE DATASET-WISE ANNUAL ANOMALY DETECTION
-- ============================================================

WITH ANNUAL_STATE_TOTALS AS (
    SELECT
        DATASET_TYPE,
        STATE_CODE,
        STATE,
        YEAR,
        SUM(VEHICLE_COUNT) AS REPORTED_VEHICLE_COUNT
    FROM SILVER_VAHAN_VEHICLE_MARKET
    GROUP BY
        DATASET_TYPE,
        STATE_CODE,
        STATE,
        YEAR
),

ANOMALY_BASE AS (
    SELECT
        DATASET_TYPE,
        STATE_CODE,
        STATE,
        YEAR,
        REPORTED_VEHICLE_COUNT,

        AVG(REPORTED_VEHICLE_COUNT) OVER (
            PARTITION BY DATASET_TYPE, STATE_CODE
        ) AS AVERAGE_VEHICLE_COUNT,

        STDDEV_SAMP(REPORTED_VEHICLE_COUNT) OVER (
            PARTITION BY DATASET_TYPE, STATE_CODE
        ) AS STANDARD_DEVIATION

    FROM ANNUAL_STATE_TOTALS
)

SELECT
    DATASET_TYPE,
    STATE_CODE,
    STATE,
    YEAR,
    REPORTED_VEHICLE_COUNT,

    ROUND(AVERAGE_VEHICLE_COUNT, 2)
        AS AVERAGE_VEHICLE_COUNT,

    ROUND(STANDARD_DEVIATION, 2)
        AS STANDARD_DEVIATION,

    ROUND(
        (
            REPORTED_VEHICLE_COUNT - AVERAGE_VEHICLE_COUNT
        ) / NULLIF(STANDARD_DEVIATION, 0),
        2
    ) AS Z_SCORE,

    CASE
        WHEN ABS(
            (
                REPORTED_VEHICLE_COUNT - AVERAGE_VEHICLE_COUNT
            ) / NULLIF(STANDARD_DEVIATION, 0)
        ) >= 2
        THEN 'ANOMALY'
        ELSE 'NORMAL'
    END AS ANOMALY_STATUS

FROM ANOMALY_BASE
ORDER BY
    DATASET_TYPE,
    STATE,
    YEAR;


-- ============================================================
-- 32. HIGH-PRIORITY STATE-WISE ANOMALIES
-- ============================================================

WITH ANNUAL_STATE_TOTALS AS (
    SELECT
        DATASET_TYPE,
        STATE_CODE,
        STATE,
        YEAR,
        SUM(VEHICLE_COUNT) AS REPORTED_VEHICLE_COUNT
    FROM SILVER_VAHAN_VEHICLE_MARKET
    GROUP BY
        DATASET_TYPE,
        STATE_CODE,
        STATE,
        YEAR
),

ANOMALY_BASE AS (
    SELECT
        DATASET_TYPE,
        STATE_CODE,
        STATE,
        YEAR,
        REPORTED_VEHICLE_COUNT,

        AVG(REPORTED_VEHICLE_COUNT) OVER (
            PARTITION BY DATASET_TYPE, STATE_CODE
        ) AS AVERAGE_VEHICLE_COUNT,

        STDDEV_SAMP(REPORTED_VEHICLE_COUNT) OVER (
            PARTITION BY DATASET_TYPE, STATE_CODE
        ) AS STANDARD_DEVIATION

    FROM ANNUAL_STATE_TOTALS
),

ANOMALY_RESULTS AS (
    SELECT
        DATASET_TYPE,
        STATE_CODE,
        STATE,
        YEAR,
        REPORTED_VEHICLE_COUNT,

        ROUND(
            (
                REPORTED_VEHICLE_COUNT - AVERAGE_VEHICLE_COUNT
            ) / NULLIF(STANDARD_DEVIATION, 0),
            2
        ) AS Z_SCORE

    FROM ANOMALY_BASE
)

SELECT
    DATASET_TYPE,
    STATE_CODE,
    STATE,
    YEAR,
    REPORTED_VEHICLE_COUNT,
    Z_SCORE,

    CASE
        WHEN Z_SCORE >= 2 THEN 'HIGH_SPIKE'
        WHEN Z_SCORE <= -2 THEN 'HIGH_DROP'
        ELSE 'NORMAL'
    END AS ANOMALY_TYPE

FROM ANOMALY_RESULTS
WHERE ABS(Z_SCORE) >= 2
ORDER BY ABS(Z_SCORE) DESC;


-- ============================================================
-- 33. CATEGORY-FUEL YEARLY CORRELATION
-- ============================================================

WITH CATEGORY_YEARLY AS (
    SELECT
        YEAR,
        SUM(VEHICLE_COUNT) AS CATEGORY_VEHICLE_COUNT
    FROM FACT_CATEGORY
    GROUP BY YEAR
),

FUEL_YEARLY AS (
    SELECT
        YEAR,
        SUM(VEHICLE_COUNT) AS FUEL_VEHICLE_COUNT
    FROM FACT_FUEL
    GROUP BY YEAR
),

YEARLY_COMPARISON AS (
    SELECT
        C.YEAR,
        C.CATEGORY_VEHICLE_COUNT,
        F.FUEL_VEHICLE_COUNT
    FROM CATEGORY_YEARLY C
    INNER JOIN FUEL_YEARLY F
        ON C.YEAR = F.YEAR
)

SELECT
    CORR(
        CATEGORY_VEHICLE_COUNT,
        FUEL_VEHICLE_COUNT
    ) AS CATEGORY_FUEL_CORRELATION,

    COUNT(*) AS YEAR_COUNT,

    ROUND(AVG(CATEGORY_VEHICLE_COUNT), 2)
        AS AVG_CATEGORY_VEHICLES,

    ROUND(AVG(FUEL_VEHICLE_COUNT), 2)
        AS AVG_FUEL_VEHICLES

FROM YEARLY_COMPARISON;


-- ============================================================
-- 34. FUEL-MANUFACTURER YEARLY CORRELATION
-- ============================================================

WITH FUEL_YEARLY AS (
    SELECT
        YEAR,
        SUM(VEHICLE_COUNT) AS FUEL_VEHICLE_COUNT
    FROM FACT_FUEL
    GROUP BY YEAR
),

MANUFACTURER_YEARLY AS (
    SELECT
        YEAR,
        SUM(VEHICLE_COUNT) AS MANUFACTURER_VEHICLE_COUNT
    FROM FACT_MANUFACTURER
    GROUP BY YEAR
),

YEARLY_COMPARISON AS (
    SELECT
        F.YEAR,
        F.FUEL_VEHICLE_COUNT,
        M.MANUFACTURER_VEHICLE_COUNT
    FROM FUEL_YEARLY F
    INNER JOIN MANUFACTURER_YEARLY M
        ON F.YEAR = M.YEAR
)

SELECT
    CORR(
        FUEL_VEHICLE_COUNT,
        MANUFACTURER_VEHICLE_COUNT
    ) AS FUEL_MANUFACTURER_CORRELATION,

    COUNT(*) AS YEAR_COUNT,

    ROUND(AVG(FUEL_VEHICLE_COUNT), 2)
        AS AVG_FUEL_VEHICLES,

    ROUND(AVG(MANUFACTURER_VEHICLE_COUNT), 2)
        AS AVG_MANUFACTURER_VEHICLES

FROM YEARLY_COMPARISON;


-- ============================================================
-- 35. CATEGORY-MANUFACTURER YEARLY CORRELATION
-- ============================================================

WITH CATEGORY_YEARLY AS (
    SELECT
        YEAR,
        SUM(VEHICLE_COUNT) AS CATEGORY_VEHICLE_COUNT
    FROM FACT_CATEGORY
    GROUP BY YEAR
),

MANUFACTURER_YEARLY AS (
    SELECT
        YEAR,
        SUM(VEHICLE_COUNT) AS MANUFACTURER_VEHICLE_COUNT
    FROM FACT_MANUFACTURER
    GROUP BY YEAR
),

YEARLY_COMPARISON AS (
    SELECT
        C.YEAR,
        C.CATEGORY_VEHICLE_COUNT,
        M.MANUFACTURER_VEHICLE_COUNT
    FROM CATEGORY_YEARLY C
    INNER JOIN MANUFACTURER_YEARLY M
        ON C.YEAR = M.YEAR
)

SELECT
    CORR(
        CATEGORY_VEHICLE_COUNT,
        MANUFACTURER_VEHICLE_COUNT
    ) AS CATEGORY_MANUFACTURER_CORRELATION,

    COUNT(*) AS YEAR_COUNT,

    ROUND(AVG(CATEGORY_VEHICLE_COUNT), 2)
        AS AVG_CATEGORY_VEHICLES,

    ROUND(AVG(MANUFACTURER_VEHICLE_COUNT), 2)
        AS AVG_MANUFACTURER_VEHICLES

FROM YEARLY_COMPARISON;


-- ============================================================
-- END OF SQL ANALYTICS QUERIES
-- ============================================================