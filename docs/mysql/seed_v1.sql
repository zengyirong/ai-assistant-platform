-- AI Assistant Platform — Seed V1 (local/dev)
-- Requires: ddl_v1.sql already applied
-- Password placeholder: replace password_hash before production use.
-- Demo passwords (local only):
--   admin / Admin@123456  (ADMIN)
--   demo  / Demo@123456   (USER)
-- bcrypt hash generated via app.core.security.hash_password

USE ai_assistant;

SET @org_id   = '11111111-1111-1111-1111-111111111111';
SET @admin_id = '22222222-2222-2222-2222-222222222222';
SET @demo_id  = '77777777-7777-7777-7777-777777777777';
SET @role_admin = '33333333-3333-3333-3333-333333333333';
SET @role_user  = '44444444-4444-4444-4444-444444444444';
SET @space_id = '55555555-5555-5555-5555-555555555555';
SET @ai_cfg_id = '66666666-6666-6666-6666-666666666666';

INSERT INTO organization (id, name, code, status)
VALUES (@org_id, 'Demo Organization', 'demo', 'ACTIVE')
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO sys_role (id, org_id, code, name, status) VALUES
  (@role_admin, @org_id, 'ADMIN', 'Administrator', 'ACTIVE'),
  (@role_user,  @org_id, 'USER',  'User',          'ACTIVE')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Minimal permissions (extend in Phase 1)
INSERT INTO sys_permission (id, code, name, type, parent_id) VALUES
  ('p0000000-0000-0000-0000-000000000001', 'knowledge:list',   'Knowledge List',   'API', NULL),
  ('p0000000-0000-0000-0000-000000000002', 'knowledge:create', 'Knowledge Create', 'API', NULL),
  ('p0000000-0000-0000-0000-000000000003', 'knowledge:update', 'Knowledge Update', 'API', NULL),
  ('p0000000-0000-0000-0000-000000000004', 'knowledge:delete', 'Knowledge Delete', 'API', NULL),
  ('p0000000-0000-0000-0000-000000000005', 'document:list',    'Document List',    'API', NULL),
  ('p0000000-0000-0000-0000-000000000006', 'document:upload',  'Document Upload',  'API', NULL),
  ('p0000000-0000-0000-0000-000000000007', 'document:delete',  'Document Delete',  'API', NULL),
  ('p0000000-0000-0000-0000-000000000008', 'document:retry',   'Document Retry',   'API', NULL),
  ('p0000000-0000-0000-0000-000000000009', 'conversation:list',   'Conversation List',   'API', NULL),
  ('p0000000-0000-0000-0000-00000000000a', 'conversation:create', 'Conversation Create', 'API', NULL),
  ('p0000000-0000-0000-0000-00000000000b', 'conversation:delete', 'Conversation Delete', 'API', NULL)
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- ADMIN gets all listed permissions
INSERT INTO sys_role_permission (id, role_id, permission_id)
SELECT UUID(), @role_admin, id FROM sys_permission
ON DUPLICATE KEY UPDATE role_id = role_id;

-- USER: list + upload + conversation
INSERT INTO sys_role_permission (id, role_id, permission_id) VALUES
  (UUID(), @role_user, 'p0000000-0000-0000-0000-000000000001'),
  (UUID(), @role_user, 'p0000000-0000-0000-0000-000000000005'),
  (UUID(), @role_user, 'p0000000-0000-0000-0000-000000000006'),
  (UUID(), @role_user, 'p0000000-0000-0000-0000-000000000009'),
  (UUID(), @role_user, 'p0000000-0000-0000-0000-00000000000a')
ON DUPLICATE KEY UPDATE role_id = role_id;

-- bcrypt for Admin@123456 (cost 12)
INSERT INTO sys_user (id, org_id, username, password_hash, nickname, email, status)
VALUES (
  @admin_id,
  @org_id,
  'admin',
  '$2b$12$96jyybMfILgf.vxno4Ub6u/n.z7q7nljrUyMUyT2pp/w.rkmgfNbO',
  'Admin',
  'admin@example.com',
  'ACTIVE'
)
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  nickname = VALUES(nickname);

INSERT INTO sys_user_role (id, user_id, role_id)
VALUES (UUID(), @admin_id, @role_admin)
ON DUPLICATE KEY UPDATE user_id = VALUES(user_id);

-- bcrypt for Demo@123456 (cost 12) — ordinary USER for member demos
INSERT INTO sys_user (id, org_id, username, password_hash, nickname, email, status)
VALUES (
  @demo_id,
  @org_id,
  'demo',
  '$2b$12$uXq19TZ9Er1ugw7vJqDwCuVITN9f49gthJWVbr1Z3CLJ9uN1lac.m',
  'Demo User',
  'demo@example.com',
  'ACTIVE'
)
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  nickname = VALUES(nickname);

INSERT INTO sys_user_role (id, user_id, role_id)
VALUES (UUID(), @demo_id, @role_user)
ON DUPLICATE KEY UPDATE user_id = VALUES(user_id);

INSERT INTO space (id, org_id, name, description, is_default, owner_id)
VALUES (@space_id, @org_id, '默认空间', 'Organization default space', 1, @admin_id)
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO space_member (id, space_id, user_id, role)
VALUES (UUID(), @space_id, @admin_id, 'OWNER')
ON DUPLICATE KEY UPDATE role = VALUES(role);

INSERT INTO space_member (id, space_id, user_id, role)
VALUES (UUID(), @space_id, @demo_id, 'MEMBER')
ON DUPLICATE KEY UPDATE role = VALUES(role);

-- Align embedding_dimension with real model before indexing vectors
INSERT INTO platform_ai_config (
  id, org_id, embedding_provider, embedding_model, embedding_dimension, is_active
) VALUES (
  @ai_cfg_id,
  @org_id,
  'openai_compatible',
  'text-embedding-3-small',
  1536,
  1
)
ON DUPLICATE KEY UPDATE embedding_model = VALUES(embedding_model);
