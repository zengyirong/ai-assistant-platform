# 里程碑 M7 — 下一目标规划（系统管理 / 完整 RBAC 闭环）

> 前置：[M6 完成说明](./milestone-M6-completion.md) 已验收（一期 RAG 底座收口）  
> 依据：Phase 0.5 IA、Phase 0 `sys_*` 表、产品规划 V2 §11 RBAC；前端参考 [Vben 系统管理](https://www.vben.pro/#/system/)  
> 日期：2026-09-14  
> 状态：**待启动**

---

## 1. 一句话目标

**补齐系统管理面，打通「用户 → 角色 → 菜单/权限 → 前端可见 + API 鉴权」闭环**；复用 Vben Admin 5 系统管理交互，**不含部门**。

---

## 2. RBAC 闭环（本里程碑要达成）

```text
sys_user
   ↓ 绑定
sys_user_role → sys_role
   ↓ 绑定
sys_role_permission → sys_permission
                         ├── type=MENU   → 侧栏可见 / 路由准入
                         ├── type=BUTTON → 按钮显隐（可选薄做）
                         └── type=API    → 后端接口鉴权（已有种子权限码）
```

登录后 `/auth/me` 返回 `roles` + `permissions`；前端按权限生成/过滤菜单；后端继续 `require_permissions` / ADMIN 校验。

---

## 3. Must（必须）

### 3.1 后端 Admin API（本 org，仅 ADMIN）

| 域 | 能力 |
|---|---|
| **用户** | 列表（含停用）/ 创建 / 更新（昵称/状态）/ 重置密码 / 分配角色；沿用并扩展 M6 `POST /users` |
| **角色** | 列表 / 创建 / 更新 / 启停；绑定权限（MENU+API+BUTTON） |
| **菜单（权限树）** | 以 `sys_permission` 为真源：树形 CRUD（`type=MENU` 为主，可挂 BUTTON）；角色勾选菜单+API |
| **空间** | 管理页对接已有 Space API（列表/创建/改/成员）；与 IA 一致 |
| **审计** | 已有 M5 页；侧栏归入「系统管理」分组即可 |

### 3.2 菜单模型（对齐规划，扩展字段）

现有 `sys_permission(code, name, type, parent_id)` **不够驱动 Vben 菜单**。M7 用 Alembic **扩展列**（不另建部门表）：

```text
path          # 路由 path，如 /system/user
component     # 前端组件标识（可选，frontend 模式可空）
icon          # 图标名
sort_order    # 排序
visible       # 是否显示在侧栏
status        # ACTIVE / DISABLED
```

种子：把现有前端路由（问答 / 知识库 / 系统管理子页）写入 MENU 权限树，并挂到 ADMIN（及按需 USER）。

### 3.3 前端（Vben UI，裁剪部门）

- 启用「系统管理」一级菜单：用户 / 角色 / **菜单** / 空间 / 审计  
- UI 参考 [Vben system](https://www.vben.pro/#/system/)：**去掉部门管理与用户页左侧部门树**  
- `accessMode`：优先 **backend**（`/menu/all` 按当前用户权限返回菜单树）；或 frontend + 权限码过滤（二选一，开工时定一种并写进完成说明）  
- 角色页：权限树勾选（菜单 + API）  

### 3.4 回归

- `ruff` + `pytest`；ADMIN/USER 登录后菜单差异可手测  
- 契约：`docs/api.md` 增补 Admin 端点  

---

## 4. Should

- 按钮级权限（`type=BUTTON`）在 1～2 个关键页落地（如「新建用户」）  
- 菜单管理页支持拖拽排序（可降级为数字 `sort_order`）  
- Citation 小修（M6 结转，非本里程碑主线）  

---

## 5. Won’t

| 项 | 原因 |
|---|---|
| **部门 / 组织树** | 规划与 DDL 均无；协作边界用 Space |
| 多租户 Organization CRUD | 一期 org 种子绑定 |
| 完整动态组件热插拔 / 在线配任意路由 | 菜单管理限于已注册业务页 + 权限码 |
| Redis / Celery / MinIO / OCR（P2） | 不膨胀 |

---

## 6. 与 Phase 0.5 IA 对齐（修订）

原 IA：用户 / 角色 / 空间 / 审计。  

**M7 起增加「菜单管理」**，形成完整 RBAC 管理面：

```text
系统管理
├── 用户管理
├── 角色管理
├── 菜单管理      ← 新增（权限树 / MENU）
├── 空间管理
└── 审计日志
```

---

## 7. 退出标准（草案）

```text
□ ADMIN 可管理本 org 用户、角色、菜单权限树
□ 角色变更后，用户重新登录（或刷新权限）菜单与 API 权限一致
□ 无部门相关 UI/API/表
□ 空间管理页可用；审计仍在系统管理下
□ 自动化测试覆盖关键 Admin API；plan 完成说明
```

---

## 8. 建议实现顺序

```text
1. Alembic 扩展 sys_permission 菜单字段 + seed 菜单树
2. 菜单树 API（CRUD + /menu/all）
3. 角色 ↔ 权限绑定 API + UI
4. 用户管理 UI（扩现有 API）
5. 空间管理页归入系统管理
6. 侧栏/accessMode 打通闭环
```

---

## 9. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 初版：系统管理薄版 + **菜单入闭环**；明确无部门 |
