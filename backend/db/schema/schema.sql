SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS frame_precedent_links;
DROP TABLE IF EXISTS frame_principles;
DROP TABLE IF EXISTS frame_key_facts;
DROP TABLE IF EXISTS interpretation_frames;
DROP TABLE IF EXISTS precedent_citations;

DROP TABLE IF EXISTS case_principles;
DROP TABLE IF EXISTS case_precedents;
DROP TABLE IF EXISTS case_keywords;
DROP TABLE IF EXISTS case_clauses;
DROP TABLE IF EXISTS case_judges;
DROP TABLE IF EXISTS case_chunks;

DROP TABLE IF EXISTS cases;
DROP TABLE IF EXISTS precedents;
DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS clauses;
DROP TABLE IF EXISTS judges;
DROP TABLE IF EXISTS courts;

DROP TABLE IF EXISTS constitution_clauses;

DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_roles;

-- -----------------------------------------------------------------------------
-- 1) Constitution clauses
--    - article: e.g. "10", "12", "14A"
--    - subclause: JSON "clause" field; empty string when JSON clause is null
--    - clause_text: authoritative text for that sub-clause row
-- -----------------------------------------------------------------------------
CREATE TABLE constitution_clauses (
  clause_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  article VARCHAR(16) NOT NULL,
  subclause VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'Empty string = single row per article when JSON clause is null',
  clause_text TEXT NOT NULL,
  PRIMARY KEY (clause_id),
  UNIQUE KEY uq_constitution_article_subclause (article, subclause),
  KEY idx_constitution_article (article)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Sri Lanka Constitution FR excerpt; seed from articles.json';

-- -----------------------------------------------------------------------------
-- 2) Cases
-- -----------------------------------------------------------------------------
CREATE TABLE cases (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  case_identifier VARCHAR(512) NOT NULL COMMENT 'Visible corpus id from frame JSON (e.g. citation style); use for display / web search, not as join PK',
  case_title TEXT NOT NULL,
  court_name VARCHAR(255) NULL,
  decision_date DATE NULL,
  source_citation TEXT NULL,
  pdf_relative_path VARCHAR(1024) NULL COMMENT 'Relative to app-configured PDF root; NULL until ingest supplies path',
  ingest_metadata JSON NULL COMMENT 'Optional snapshot: manifest / pipeline fields',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_cases_case_identifier (case_identifier),
  KEY idx_cases_decision_date (decision_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3) Interpretation frames: one row per ranked unit
-- -----------------------------------------------------------------------------
CREATE TABLE interpretation_frames (
  frame_id VARCHAR(255) NOT NULL,
  case_id BIGINT UNSIGNED NOT NULL COMMENT 'FK cases.id — use this for backend joins and GET-by-internal-id',
  clause_id BIGINT UNSIGNED NOT NULL COMMENT 'FK constitution_clauses: which article/subclause this frame interprets',
  created_at DATE NULL,
  annotator_id VARCHAR(255) NULL,
  source_dataset VARCHAR(255) NULL,
  source_notes TEXT NULL,
  -- case_context
  legal_issue TEXT NULL,
  petitioner_claim TEXT NULL,
  respondent_argument TEXT NULL,
  -- reasoning (scalar)
  interpretation_summary TEXT NULL,
  application_to_facts TEXT NULL,
  -- outcome
  holding TEXT NULL,
  disposition VARCHAR(32) NULL COMMENT 'e.g. dismissed, granted, allowed_in_part, other',
  remedy_or_orders TEXT NULL,
  -- link_explanation
  why_this_clause_matters TEXT NULL,
  relevance_level VARCHAR(16) NULL COMMENT 'high | medium | low',
  match_type VARCHAR(32) NULL COMMENT 'direct_interpretation | application_only | mentioned_only',
  -- evidence
  evidence_excerpt TEXT NULL,
  evidence_field VARCHAR(64) NULL COMMENT 'e.g. full_text, interpretation_summary, principles_established',
  evidence_start_char INT NULL,
  evidence_end_char INT NULL,
  PRIMARY KEY (frame_id),
  KEY idx_frames_case (case_id),
  KEY idx_frames_clause (clause_id),
  CONSTRAINT fk_frames_case
    FOREIGN KEY (case_id) REFERENCES cases (id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_frames_constitution_clause
    FOREIGN KEY (clause_id) REFERENCES constitution_clauses (clause_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE frame_key_facts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  frame_id VARCHAR(255) NOT NULL,
  sort_order INT UNSIGNED NOT NULL DEFAULT 0,
  fact_text TEXT NOT NULL,
  PRIMARY KEY (id),
  KEY idx_frame_key_facts_frame (frame_id),
  CONSTRAINT fk_frame_key_facts_frame
    FOREIGN KEY (frame_id) REFERENCES interpretation_frames (frame_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE frame_principles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  frame_id VARCHAR(255) NOT NULL,
  sort_order INT UNSIGNED NOT NULL DEFAULT 0,
  principle_text TEXT NOT NULL,
  PRIMARY KEY (id),
  KEY idx_frame_principles_frame (frame_id),
  CONSTRAINT fk_frame_principles_frame
    FOREIGN KEY (frame_id) REFERENCES interpretation_frames (frame_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Normalized precedent citations (dedupe across frames)
CREATE TABLE precedent_citations (
  precedent_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  citation VARCHAR(512) NOT NULL,
  PRIMARY KEY (precedent_id),
  UNIQUE KEY uq_precedent_citation (citation(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE frame_precedent_links (
  frame_id VARCHAR(255) NOT NULL,
  precedent_id BIGINT UNSIGNED NOT NULL,
  sort_order INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (frame_id, precedent_id),
  KEY idx_frame_precedent_precedent (precedent_id),
  CONSTRAINT fk_frame_prec_frame
    FOREIGN KEY (frame_id) REFERENCES interpretation_frames (frame_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_frame_prec_precedent
    FOREIGN KEY (precedent_id) REFERENCES precedent_citations (precedent_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4) Auth
-- -----------------------------------------------------------------------------
CREATE TABLE user_roles (
  role_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_user_roles_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO user_roles (name) VALUES ('admin'), ('user');

CREATE TABLE users (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role_id INT UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  last_login DATETIME(6) NULL DEFAULT NULL,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_users_username (username),
  CONSTRAINT fk_users_role
    FOREIGN KEY (role_id) REFERENCES user_roles (role_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5) Chat
-- -----------------------------------------------------------------------------
CREATE TABLE conversations (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  conversation_id VARCHAR(255) NOT NULL COMMENT 'Client-facing id (e.g. UUID)',
  user_id BIGINT UNSIGNED NULL,
  title VARCHAR(255) NULL COMMENT 'Auto-generated title from first user message',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  active TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_conversations_conversation_id (conversation_id),
  KEY idx_conversations_user (user_id),
  CONSTRAINT fk_conversations_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE messages (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  conversation_id BIGINT UNSIGNED NOT NULL,
  role VARCHAR(32) NOT NULL COMMENT 'user | assistant',
  content LONGTEXT NOT NULL,
  retrieval_result JSON NULL COMMENT 'Ranked interpretation frames / search payload for assistant messages',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_messages_conversation (conversation_id),
  CONSTRAINT fk_messages_conversation
    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6) Audit logs
-- -----------------------------------------------------------------------------
CREATE TABLE audit_logs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  user_id BIGINT UNSIGNED NULL,
  username VARCHAR(255) NULL,
  action VARCHAR(64) NOT NULL,
  resource_type VARCHAR(64) NULL,
  resource_id VARCHAR(255) NULL,
  details JSON NULL,
  success TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  KEY idx_audit_user (user_id),
  KEY idx_audit_action (action),
  KEY idx_audit_created (created_at),
  KEY idx_audit_resource (resource_type, resource_id),
  CONSTRAINT fk_audit_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
