-- Migration: add retrieval_result to messages (for persisting case results per assistant message).
-- Run this on existing databases that were created before this column was added.

ALTER TABLE messages
  ADD COLUMN retrieval_result JSON NULL
  COMMENT 'Case results for assistant messages (search_cases tool).'
  AFTER content;
