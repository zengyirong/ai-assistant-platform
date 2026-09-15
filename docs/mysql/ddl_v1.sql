-- AI Assistant Platform — MySQL DDL V1
-- Charset: utf8mb4 | Engine: InnoDB
-- Source: Phase0 系统设计 + v2-planning-review R1–R6
--
-- Prefer Alembic for new environments:
--   cd backend && alembic upgrade head
--   then apply seed_v1.sql
-- This file is a readable reference and Docker MySQL init fallback.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS ai_assistant
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE ai_assistant;

-- ---------------------------------------------------------------------------
-- organization
-- ---------------------------------------------------------------------------
CREATE TABLE organization (
  id         CHAR(36)     NOT NULL,
  name       VARCHAR(128) NOT NULL,
  code       VARCHAR(64)  NOT NULL,
  status     VARCHAR(32)  NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_org_code (code),
  KEY idx_org_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- sys_permission
-- ---------------------------------------------------------------------------
CREATE TABLE sys_permission (
  id         CHAR(36)     NOT NULL,
  code       VARCHAR(128) NOT NULL,
  name       VARCHAR(128) NOT NULL,
  type       VARCHAR(32)  NOT NULL,
  parent_id  CHAR(36)     NULL,
  path       VARCHAR(255) NULL,
  component  VARCHAR(255) NULL,
  icon       VARCHAR(128) NULL,
  sort_order INT          NOT NULL DEFAULT 0,
  visible    TINYINT      NOT NULL DEFAULT 1,
  status     VARCHAR(32)  NOT NULL DEFAULT 'ACTIVE',
  redirect   VARCHAR(255) NULL,
  created_at DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_permission_code (code),
  KEY idx_permission_parent (parent_id),
  KEY idx_permission_type (type),
  CONSTRAINT fk_permission_parent
    FOREIGN KEY (parent_id) REFERENCES sys_permission (id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- sys_role
-- ---------------------------------------------------------------------------
CREATE TABLE sys_role (
  id         CHAR(36)     NOT NULL,
  org_id     CHAR(36)     NOT NULL,
  code       VARCHAR(64)  NOT NULL,
  name       VARCHAR(128) NOT NULL,
  status     VARCHAR(32)  NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_org_code (org_id, code),
  KEY idx_role_org (org_id),
  CONSTRAINT fk_role_org
    FOREIGN KEY (org_id) REFERENCES organization (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- sys_user
-- ---------------------------------------------------------------------------
CREATE TABLE sys_user (
  id            CHAR(36)     NOT NULL,
  org_id        CHAR(36)     NOT NULL,
  username      VARCHAR(64)  NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  nickname      VARCHAR(128) NULL,
  email         VARCHAR(255) NULL,
  status        VARCHAR(32)  NOT NULL DEFAULT 'ACTIVE',
  created_at    DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at    DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_org_username (org_id, username),
  KEY idx_user_org (org_id),
  KEY idx_user_status (status),
  CONSTRAINT fk_user_org
    FOREIGN KEY (org_id) REFERENCES organization (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- sys_user_role / sys_role_permission
-- ---------------------------------------------------------------------------
CREATE TABLE sys_user_role (
  id         CHAR(36)    NOT NULL,
  user_id    CHAR(36)    NOT NULL,
  role_id    CHAR(36)    NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_role (user_id, role_id),
  KEY idx_user_role_role (role_id),
  CONSTRAINT fk_user_role_user
    FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE,
  CONSTRAINT fk_user_role_role
    FOREIGN KEY (role_id) REFERENCES sys_role (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sys_role_permission (
  id            CHAR(36)    NOT NULL,
  role_id       CHAR(36)    NOT NULL,
  permission_id CHAR(36)    NOT NULL,
  created_at    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_permission (role_id, permission_id),
  KEY idx_role_permission_perm (permission_id),
  CONSTRAINT fk_role_permission_role
    FOREIGN KEY (role_id) REFERENCES sys_role (id) ON DELETE CASCADE,
  CONSTRAINT fk_role_permission_perm
    FOREIGN KEY (permission_id) REFERENCES sys_permission (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- space / space_member
-- ---------------------------------------------------------------------------
CREATE TABLE space (
  id                 CHAR(36)     NOT NULL,
  org_id             CHAR(36)     NOT NULL,
  name               VARCHAR(128) NOT NULL,
  description        VARCHAR(512) NULL,
  is_default         TINYINT(1)   NOT NULL DEFAULT 0,
  owner_id           CHAR(36)     NULL,
  -- 仅 default space 写入 org_id，保证每 org 至多一个 default
  default_space_key  CHAR(36) GENERATED ALWAYS AS (
    CASE WHEN is_default = 1 THEN org_id ELSE NULL END
  ) STORED,
  created_at         DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at         DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_space_org_default_key (default_space_key),
  KEY idx_space_org (org_id),
  KEY idx_space_owner (owner_id),
  CONSTRAINT fk_space_org
    FOREIGN KEY (org_id) REFERENCES organization (id),
  CONSTRAINT fk_space_owner
    FOREIGN KEY (owner_id) REFERENCES sys_user (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE space_member (
  id         CHAR(36)    NOT NULL,
  space_id   CHAR(36)    NOT NULL,
  user_id    CHAR(36)    NOT NULL,
  role       VARCHAR(32) NOT NULL DEFAULT 'MEMBER',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_space_member (space_id, user_id),
  KEY idx_space_member_user (user_id),
  CONSTRAINT fk_space_member_space
    FOREIGN KEY (space_id) REFERENCES space (id) ON DELETE CASCADE,
  CONSTRAINT fk_space_member_user
    FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- platform_ai_config（平台级 Embedding，禁止每 KB 自选）
-- ---------------------------------------------------------------------------
CREATE TABLE platform_ai_config (
  id                   CHAR(36)     NOT NULL,
  org_id               CHAR(36)     NOT NULL,
  embedding_provider   VARCHAR(64)  NOT NULL,
  embedding_model      VARCHAR(128) NOT NULL,
  embedding_dimension  INT UNSIGNED NOT NULL,
  is_active            TINYINT(1)   NOT NULL DEFAULT 1,
  active_org_key       CHAR(36) GENERATED ALWAYS AS (
    CASE WHEN is_active = 1 THEN org_id ELSE NULL END
  ) STORED,
  created_at           DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at           DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_platform_ai_active_org (active_org_key),
  KEY idx_platform_ai_org (org_id),
  CONSTRAINT fk_platform_ai_org
    FOREIGN KEY (org_id) REFERENCES organization (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- knowledge_base / member / rag_config
-- ---------------------------------------------------------------------------
CREATE TABLE knowledge_base (
  id          CHAR(36)     NOT NULL,
  org_id      CHAR(36)     NOT NULL,
  space_id    CHAR(36)     NULL,
  name        VARCHAR(128) NOT NULL,
  description VARCHAR(1024) NULL,
  visibility  VARCHAR(32)  NOT NULL,
  status      VARCHAR(32)  NOT NULL DEFAULT 'ACTIVE',
  created_by  CHAR(36)     NOT NULL,
  created_at  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_kb_org (org_id),
  KEY idx_kb_space (space_id),
  KEY idx_kb_visibility (visibility),
  KEY idx_kb_created_by (created_by),
  CONSTRAINT fk_kb_org
    FOREIGN KEY (org_id) REFERENCES organization (id),
  CONSTRAINT fk_kb_space
    FOREIGN KEY (space_id) REFERENCES space (id) ON DELETE SET NULL,
  CONSTRAINT fk_kb_created_by
    FOREIGN KEY (created_by) REFERENCES sys_user (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE knowledge_base_member (
  id         CHAR(36)    NOT NULL,
  kb_id      CHAR(36)    NOT NULL,
  user_id    CHAR(36)    NOT NULL,
  role       VARCHAR(32) NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_kb_member (kb_id, user_id),
  KEY idx_kb_member_user (user_id),
  CONSTRAINT fk_kb_member_kb
    FOREIGN KEY (kb_id) REFERENCES knowledge_base (id) ON DELETE CASCADE,
  CONSTRAINT fk_kb_member_user
    FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rag_config (
  id               CHAR(36)       NOT NULL,
  kb_id            CHAR(36)       NOT NULL,
  chunk_strategy   VARCHAR(64)    NOT NULL DEFAULT 'recursive',
  chunk_size       INT UNSIGNED   NOT NULL DEFAULT 800,
  chunk_overlap    INT UNSIGNED   NOT NULL DEFAULT 120,
  top_k            INT UNSIGNED   NOT NULL DEFAULT 5,
  score_threshold  DECIMAL(10, 6) NULL,
  llm_model        VARCHAR(128)   NULL,
  temperature      DECIMAL(4, 2)  NOT NULL DEFAULT 0.20,
  system_prompt    TEXT           NULL,
  created_at       DATETIME(3)    NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at       DATETIME(3)    NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_rag_config_kb (kb_id),
  CONSTRAINT fk_rag_config_kb
    FOREIGN KEY (kb_id) REFERENCES knowledge_base (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- document / document_chunk / document_job
-- ---------------------------------------------------------------------------
CREATE TABLE document (
  id           CHAR(36)      NOT NULL,
  org_id       CHAR(36)      NOT NULL,
  kb_id        CHAR(36)      NOT NULL,
  file_name    VARCHAR(255)  NOT NULL,
  storage_path VARCHAR(512)  NOT NULL,
  file_hash    CHAR(64)      NOT NULL COMMENT 'SHA-256 hex of raw bytes',
  file_type    VARCHAR(32)   NOT NULL,
  file_size    BIGINT UNSIGNED NOT NULL,
  page_count   INT UNSIGNED  NULL,
  status       VARCHAR(32)   NOT NULL DEFAULT 'UPLOADED',
  created_by   CHAR(36)      NOT NULL,
  created_at   DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at   DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_document_kb_hash (kb_id, file_hash),
  KEY idx_document_org (org_id),
  KEY idx_document_kb_status (kb_id, status),
  KEY idx_document_created_by (created_by),
  CONSTRAINT fk_document_org
    FOREIGN KEY (org_id) REFERENCES organization (id),
  CONSTRAINT fk_document_kb
    FOREIGN KEY (kb_id) REFERENCES knowledge_base (id),
  CONSTRAINT fk_document_created_by
    FOREIGN KEY (created_by) REFERENCES sys_user (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE document_chunk (
  id           CHAR(36)      NOT NULL,
  org_id       CHAR(36)      NOT NULL,
  kb_id        CHAR(36)      NOT NULL,
  document_id  CHAR(36)      NOT NULL,
  chunk_index  INT UNSIGNED  NOT NULL,
  content      MEDIUMTEXT    NOT NULL,
  content_hash CHAR(64)      NOT NULL,
  page         INT UNSIGNED  NULL,
  section      VARCHAR(255)  NULL,
  token_count  INT UNSIGNED  NULL,
  created_at   DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at   DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_chunk_doc_index (document_id, chunk_index),
  KEY idx_chunk_kb (kb_id),
  KEY idx_chunk_document (document_id),
  KEY idx_chunk_content_hash (content_hash),
  KEY idx_chunk_org (org_id),
  CONSTRAINT fk_chunk_org
    FOREIGN KEY (org_id) REFERENCES organization (id),
  CONSTRAINT fk_chunk_kb
    FOREIGN KEY (kb_id) REFERENCES knowledge_base (id),
  CONSTRAINT fk_chunk_document
    FOREIGN KEY (document_id) REFERENCES document (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE document_job (
  id            CHAR(36)      NOT NULL,
  document_id   CHAR(36)      NOT NULL,
  job_type      VARCHAR(64)   NOT NULL DEFAULT 'PARSE_INDEX',
  status        VARCHAR(32)   NOT NULL DEFAULT 'PENDING',
  progress      INT UNSIGNED  NOT NULL DEFAULT 0,
  retry_count   INT UNSIGNED  NOT NULL DEFAULT 0,
  error_code    VARCHAR(64)   NULL,
  error_message VARCHAR(1024) NULL,
  started_at    DATETIME(3)   NULL,
  finished_at   DATETIME(3)   NULL,
  created_at    DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at    DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_job_document (document_id),
  KEY idx_job_status (status),
  CONSTRAINT fk_job_document
    FOREIGN KEY (document_id) REFERENCES document (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- conversation / message / citation
-- ---------------------------------------------------------------------------
CREATE TABLE conversation (
  id         CHAR(36)     NOT NULL,
  org_id     CHAR(36)     NOT NULL,
  user_id    CHAR(36)     NOT NULL,
  title      VARCHAR(255) NULL,
  kb_scope   JSON         NULL COMMENT 'accessible / selected kb_ids snapshot',
  created_at DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_conversation_org_user (org_id, user_id),
  KEY idx_conversation_user (user_id),
  CONSTRAINT fk_conversation_org
    FOREIGN KEY (org_id) REFERENCES organization (id),
  CONSTRAINT fk_conversation_user
    FOREIGN KEY (user_id) REFERENCES sys_user (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE conversation_message (
  id              CHAR(36)      NOT NULL,
  conversation_id CHAR(36)      NOT NULL,
  role            VARCHAR(32)   NOT NULL,
  content         MEDIUMTEXT    NULL,
  status          VARCHAR(32)   NOT NULL,
  request_id      CHAR(36)      NULL,
  token_input     INT UNSIGNED  NULL,
  token_output    INT UNSIGNED  NULL,
  created_at      DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at      DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_message_conversation (conversation_id),
  KEY idx_message_request (request_id),
  CONSTRAINT fk_message_conversation
    FOREIGN KEY (conversation_id) REFERENCES conversation (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE message_citation (
  id          CHAR(36)       NOT NULL,
  message_id  CHAR(36)       NOT NULL,
  document_id CHAR(36)       NOT NULL,
  chunk_id    CHAR(36)       NOT NULL,
  page        INT UNSIGNED   NULL,
  section     VARCHAR(255)   NULL,
  score       DECIMAL(10, 6) NULL,
  snippet     VARCHAR(1024)  NULL,
  sort_order  INT UNSIGNED   NOT NULL DEFAULT 0,
  created_at  DATETIME(3)    NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_citation_message (message_id, sort_order),
  KEY idx_citation_document (document_id),
  KEY idx_citation_chunk (chunk_id),
  CONSTRAINT fk_citation_message
    FOREIGN KEY (message_id) REFERENCES conversation_message (id) ON DELETE CASCADE,
  CONSTRAINT fk_citation_document
    FOREIGN KEY (document_id) REFERENCES document (id) ON DELETE CASCADE,
  CONSTRAINT fk_citation_chunk
    FOREIGN KEY (chunk_id) REFERENCES document_chunk (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- NOTE: Prefer Alembic for new environments (`alembic upgrade head`).
-- This file remains a readable reference / Docker MySQL init fallback.

-- ---------------------------------------------------------------------------
-- audit_log
-- ---------------------------------------------------------------------------
CREATE TABLE audit_log (
  id            CHAR(36)      NOT NULL,
  org_id        CHAR(36)      NULL,
  user_id       CHAR(36)      NULL,
  action        VARCHAR(64)   NOT NULL,
  resource_type VARCHAR(64)   NULL,
  resource_id   CHAR(36)      NULL,
  request_id    CHAR(36)      NULL,
  result        VARCHAR(32)   NOT NULL,
  ip            VARCHAR(64)   NULL,
  user_agent    VARCHAR(512)  NULL,
  detail        JSON          NULL,
  created_at    DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_audit_org_time (org_id, created_at),
  KEY idx_audit_user_time (user_id, created_at),
  KEY idx_audit_action (action),
  KEY idx_audit_request (request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
