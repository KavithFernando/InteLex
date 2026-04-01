-- Migration 005: persist @-mentioned (pinned) cases on user messages.
-- Stores the FrameSummary list the user explicitly referenced so it survives page refresh.

ALTER TABLE messages
  ADD COLUMN pinned_cases JSON NULL
  COMMENT 'FrameSummary list of cases @-referenced by the user in this message.'
  AFTER retrieval_result;
