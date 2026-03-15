-- Migration 001: Auth Enhancements
-- Adds last_login column to the users table.
-- Run this script once against the existing database (do NOT re-run schema.sql,
-- which would drop and recreate all tables and lose all data).

ALTER TABLE users
    ADD COLUMN last_login DATETIME(6) NULL DEFAULT NULL
    AFTER updated_at;
