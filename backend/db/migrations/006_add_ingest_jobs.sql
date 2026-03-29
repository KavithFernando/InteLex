-- Migration 006: Ingest Jobs
-- Persists admin PDF ingest job state so history survives server restarts.

CREATE TABLE ingest_jobs (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  job_id       VARCHAR(64)     NOT NULL,
  status       VARCHAR(16)     NOT NULL DEFAULT 'queued',
  submitted_at DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  filenames    JSON            NOT NULL,
  clauses      JSON            NULL,
  log          JSON            NOT NULL DEFAULT (JSON_ARRAY()),
  frames_created INT UNSIGNED  NOT NULL DEFAULT 0,
  frames_skipped INT UNSIGNED  NOT NULL DEFAULT 0,
  errors       INT UNSIGNED    NOT NULL DEFAULT 0,
  error        TEXT            NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ingest_job_id (job_id),
  KEY idx_ingest_submitted (submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
