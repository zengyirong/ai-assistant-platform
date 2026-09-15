-- MENU + BUTTON permissions (RBAC on sys_permission). Safe to re-run.
-- Requires: alembic 20260915_0003 (menu columns) + roles from seed_v1.sql

USE ai_assistant;

SET @role_admin = '33333333-3333-3333-3333-333333333333';
SET @role_user  = '44444444-4444-4444-4444-444444444444';

-- Catalog / leaf menus
INSERT INTO sys_permission (
  id, code, name, type, parent_id, path, component, icon, sort_order, visible, status, redirect
) VALUES
  ('m0000000-0000-0000-0000-000000000001', 'menu:dashboard', '工作台', 'MENU', NULL,
   '/dashboard', NULL, 'lucide:layout-dashboard', -1, 1, 'ACTIVE', '/dashboard/home'),
  ('m0000000-0000-0000-0000-000000000002', 'menu:dashboard:home', '首页', 'MENU',
   'm0000000-0000-0000-0000-000000000001',
   '/dashboard/home', '/dashboard/index', 'lucide:home', 0, 1, 'ACTIVE', NULL),

  ('m0000000-0000-0000-0000-000000000010', 'menu:chat', '智能问答', 'MENU', NULL,
   '/chat', NULL, 'lucide:message-square-text', 5, 1, 'ACTIVE', '/chat/workspace'),
  ('m0000000-0000-0000-0000-000000000011', 'menu:chat:workspace', '问答工作台', 'MENU',
   'm0000000-0000-0000-0000-000000000010',
   '/chat/workspace', '/ai-chat/index', 'lucide:bot', 0, 1, 'ACTIVE', NULL),

  ('m0000000-0000-0000-0000-000000000020', 'menu:knowledge', '知识库', 'MENU', NULL,
   '/knowledge', NULL, 'lucide:library', 10, 1, 'ACTIVE', '/knowledge/list'),
  ('m0000000-0000-0000-0000-000000000021', 'menu:knowledge:list', '知识库管理', 'MENU',
   'm0000000-0000-0000-0000-000000000020',
   '/knowledge/list', '/knowledge/list', 'lucide:folder-kanban', 0, 1, 'ACTIVE', NULL),
  ('m0000000-0000-0000-0000-000000000022', 'menu:knowledge:detail', '知识库详情', 'MENU',
   'm0000000-0000-0000-0000-000000000020',
   '/knowledge/detail/:kbId', '/knowledge/detail', 'lucide:file-text', 1, 0, 'ACTIVE', NULL),

  ('m0000000-0000-0000-0000-000000000030', 'menu:system', '系统管理', 'MENU', NULL,
   '/system', NULL, 'lucide:settings', 30, 1, 'ACTIVE', '/system/user'),
  ('m0000000-0000-0000-0000-000000000031', 'menu:system:user', '用户管理', 'MENU',
   'm0000000-0000-0000-0000-000000000030',
   '/system/user', '/system/user/index', 'lucide:users', 0, 1, 'ACTIVE', NULL),
  ('m0000000-0000-0000-0000-000000000032', 'menu:system:role', '角色管理', 'MENU',
   'm0000000-0000-0000-0000-000000000030',
   '/system/role', '/system/role/index', 'lucide:shield', 1, 1, 'ACTIVE', NULL),
  ('m0000000-0000-0000-0000-000000000033', 'menu:system:menu', '菜单管理', 'MENU',
   'm0000000-0000-0000-0000-000000000030',
   '/system/menu', '/system/menu/index', 'lucide:menu', 2, 1, 'ACTIVE', NULL),
  ('m0000000-0000-0000-0000-000000000034', 'menu:system:space', '空间管理', 'MENU',
   'm0000000-0000-0000-0000-000000000030',
   '/system/space', '/system/space/index', 'lucide:boxes', 3, 1, 'ACTIVE', NULL),
  ('m0000000-0000-0000-0000-000000000035', 'menu:system:audit', '审计日志', 'MENU',
   'm0000000-0000-0000-0000-000000000030',
   '/system/audit', '/system/audit/index', 'lucide:scroll-text', 4, 1, 'ACTIVE', NULL)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  path = VALUES(path),
  component = VALUES(component),
  icon = VALUES(icon),
  sort_order = VALUES(sort_order),
  visible = VALUES(visible),
  status = VALUES(status),
  redirect = VALUES(redirect),
  parent_id = VALUES(parent_id);

-- Thin BUTTON permissions (UI gate)
INSERT INTO sys_permission (
  id, code, name, type, parent_id, path, component, icon, sort_order, visible, status, redirect
) VALUES
  ('b0000000-0000-0000-0000-000000000031', 'btn:system:user:create', '新增用户', 'BUTTON',
   'm0000000-0000-0000-0000-000000000031',
   NULL, NULL, NULL, 0, 1, 'ACTIVE', NULL),
  ('b0000000-0000-0000-0000-000000000021', 'btn:knowledge:create', '新建知识库', 'BUTTON',
   'm0000000-0000-0000-0000-000000000021',
   NULL, NULL, NULL, 0, 1, 'ACTIVE', NULL)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  parent_id = VALUES(parent_id),
  type = VALUES(type),
  status = VALUES(status);

-- ADMIN: all MENU + BUTTON rows
INSERT INTO sys_role_permission (id, role_id, permission_id)
SELECT UUID(), @role_admin, p.id
FROM sys_permission p
WHERE p.type IN ('MENU', 'BUTTON')
  AND NOT EXISTS (
    SELECT 1 FROM sys_role_permission rp
    WHERE rp.role_id = @role_admin AND rp.permission_id = p.id
  );

-- USER: dashboard + chat + knowledge (no system)
INSERT INTO sys_role_permission (id, role_id, permission_id)
SELECT UUID(), @role_user, p.id
FROM sys_permission p
WHERE p.id IN (
  'm0000000-0000-0000-0000-000000000001',
  'm0000000-0000-0000-0000-000000000002',
  'm0000000-0000-0000-0000-000000000010',
  'm0000000-0000-0000-0000-000000000011',
  'm0000000-0000-0000-0000-000000000020',
  'm0000000-0000-0000-0000-000000000021',
  'm0000000-0000-0000-0000-000000000022'
)
AND NOT EXISTS (
  SELECT 1 FROM sys_role_permission rp
  WHERE rp.role_id = @role_user AND rp.permission_id = p.id
);
