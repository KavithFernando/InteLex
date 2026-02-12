-- Migration: add title column to conversations table (for auto-generated conversation titles).
-- Run this on existing databases that were created before this column was added.

ALTER TABLE conversations
  ADD COLUMN title VARCHAR(255) NULL
  COMMENT 'Auto-generated title from first user message'
  AFTER user_id;
