SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1) Reference tables
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS case_principles;
DROP TABLE IF EXISTS case_precedents;
DROP TABLE IF EXISTS case_keywords;
DROP TABLE IF EXISTS case_clauses;
DROP TABLE IF EXISTS case_judges;
DROP TABLE IF EXISTS cases;
DROP TABLE IF EXISTS precedents;
DROP TABLE IF EXISTS keywords;
DROP TABLE IF EXISTS clauses;
DROP TABLE IF EXISTS judges;
DROP TABLE IF EXISTS courts;
DROP TABLE IF EXISTS case_chunks;

CREATE TABLE courts (
  court_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  PRIMARY KEY (court_id),
  UNIQUE KEY uq_courts_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE judges (
  judge_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  PRIMARY KEY (judge_id),
  UNIQUE KEY uq_judges_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE clauses (
  clause_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  article VARCHAR(50) NOT NULL,
  text TEXT NOT NULL,
  PRIMARY KEY (clause_id),
  UNIQUE KEY uq_clauses_article_text (article, text(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE keywords (
  keyword_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  keyword VARCHAR(255) NOT NULL,
  PRIMARY KEY (keyword_id),
  UNIQUE KEY uq_keywords_keyword (keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE precedents (
  precedent_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  citation VARCHAR(255) NOT NULL,
  PRIMARY KEY (precedent_id),
  UNIQUE KEY uq_precedents_citation (citation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) Main cases table
CREATE TABLE cases (
  case_id VARCHAR(255) NOT NULL,     -- e.g., "SC_FR_310_1997"
  case_title TEXT NOT NULL,
  court_id BIGINT UNSIGNED NOT NULL,
  decision_date DATE NULL,
  legal_issue TEXT,
  petitioner_claim TEXT,
  respondent_argument TEXT,
  interpretation_summary TEXT,
  outcome TEXT,
  source TEXT,
  full_text LONGTEXT NULL,         -- entire body of case report (2-5 pages)
  PRIMARY KEY (case_id),
  KEY idx_cases_court_date (court_id, decision_date),
  CONSTRAINT fk_cases_court
    FOREIGN KEY (court_id) REFERENCES courts(court_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) Many-to-many relationships
CREATE TABLE case_judges (
  case_id VARCHAR(255) NOT NULL,
  judge_id BIGINT UNSIGNED NOT NULL,
  judge_order INT NULL,
  PRIMARY KEY (case_id, judge_id),
  KEY idx_case_judges_judge (judge_id),
  CONSTRAINT fk_case_judges_case
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_case_judges_judge
    FOREIGN KEY (judge_id) REFERENCES judges(judge_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE case_clauses (
  case_id VARCHAR(255) NOT NULL,
  clause_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (case_id, clause_id),
  KEY idx_case_clauses_clause (clause_id),
  CONSTRAINT fk_case_clauses_case
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_case_clauses_clause
    FOREIGN KEY (clause_id) REFERENCES clauses(clause_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE case_keywords (
  case_id VARCHAR(255) NOT NULL,
  keyword_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (case_id, keyword_id),
  KEY idx_case_keywords_keyword (keyword_id),
  CONSTRAINT fk_case_keywords_case
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_case_keywords_keyword
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE case_precedents (
  case_id VARCHAR(255) NOT NULL,
  precedent_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (case_id, precedent_id),
  KEY idx_case_precedents_prec (precedent_id),
  CONSTRAINT fk_case_precedents_case
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_case_precedents_prec
    FOREIGN KEY (precedent_id) REFERENCES precedents(precedent_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4) Principles are case-specific list items
CREATE TABLE case_principles (
  principle_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  case_id VARCHAR(255) NOT NULL,
  principle_text TEXT NOT NULL,
  principle_order INT NULL,
  PRIMARY KEY (principle_id),
  KEY idx_case_principles_case (case_id),
  CONSTRAINT fk_case_principles_case
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5) Case chunks table
CREATE TABLE case_chunks (
  chunk_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  case_id VARCHAR(255) NOT NULL,
  faiss_id BIGINT UNSIGNED NOT NULL,
  chunk_text LONGTEXT NOT NULL,
  start_word INT NULL,
  end_word INT NULL,
  start_char INT NULL,
  end_char INT NULL,
  word_count INT NULL,
  PRIMARY KEY (chunk_id),
  UNIQUE KEY uq_case_chunks_faiss (faiss_id),
  KEY idx_case_chunks_case (case_id),
  CONSTRAINT fk_case_chunks_case
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6) User roles and users (auth)
CREATE TABLE user_roles (
  role_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_user_roles_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
    FOREIGN KEY (role_id) REFERENCES user_roles(role_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7) Conversations and messages (chat history)
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
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE messages (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  conversation_id BIGINT UNSIGNED NOT NULL,
  role VARCHAR(32) NOT NULL COMMENT 'user | assistant',
  content LONGTEXT NOT NULL,
  retrieval_result JSON NULL COMMENT 'Case results for assistant messages (search_cases tool).',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_messages_conversation (conversation_id),
  CONSTRAINT fk_messages_conversation
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8) Audit logs
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
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9) Useful indexes for search/filtering
CREATE INDEX idx_clauses_article ON clauses(article);

SET FOREIGN_KEY_CHECKS = 1;
