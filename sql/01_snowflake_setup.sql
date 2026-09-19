-- ============================================================
-- 01_SNOWFLAKE_SETUP.sql
-- VAHAN Vehicle Market Intelligence Platform
-- Purpose: Create database, schema, warehouse, stage,
--          and pipeline validation summary table
-- ============================================================


-- ============================================================
-- 1. Create Database
-- ============================================================

CREATE DATABASE IF NOT EXISTS VAHAN_MARKET_DB;


-- ============================================================
-- 2. Select Database
-- ============================================================

USE DATABASE VAHAN_MARKET_DB;


-- ============================================================
-- 3. Create Schema
-- ============================================================

CREATE SCHEMA IF NOT EXISTS MARKET_SCHEMA;


-- ============================================================
-- 4. Select Schema
-- ============================================================

USE SCHEMA MARKET_SCHEMA;


-- ============================================================
-- 5. Create Warehouse
-- ============================================================

CREATE WAREHOUSE IF NOT EXISTS VAHAN_WH
WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;


-- ============================================================
-- 6. Use Warehouse
-- ============================================================

USE WAREHOUSE VAHAN_WH;


-- ============================================================
-- 7. Create Silver Stage
-- ============================================================

CREATE STAGE IF NOT EXISTS SILVER_STAGE;


-- ============================================================
-- 8. Create Pipeline Validation Summary Table
-- ============================================================

CREATE TABLE IF NOT EXISTS PIPELINE_VALIDATION_SUMMARY (
    METRIC_NAME VARCHAR(100),
    METRIC_VALUE VARCHAR(100),
    STATUS VARCHAR(20),
    VALIDATION_DATE TIMESTAMP_NTZ
);


-- ============================================================
-- 9. Verify Database
-- ============================================================

SHOW DATABASES;


-- ============================================================
-- 10. Verify Schema
-- ============================================================

SHOW SCHEMAS IN DATABASE VAHAN_MARKET_DB;


-- ============================================================
-- 11. Verify Warehouse
-- ============================================================

SHOW WAREHOUSES;


-- ============================================================
-- 12. Verify Silver Stage
-- ============================================================

SHOW STAGES;


-- ============================================================
-- 13. Verify Validation Summary Table
-- ============================================================

SHOW TABLES LIKE 'PIPELINE_VALIDATION_SUMMARY';


-- ============================================================
-- 14. Final Environment Check
-- ============================================================

SELECT
    CURRENT_DATABASE() AS CURRENT_DATABASE,
    CURRENT_SCHEMA() AS CURRENT_SCHEMA,
    CURRENT_WAREHOUSE() AS CURRENT_WAREHOUSE;