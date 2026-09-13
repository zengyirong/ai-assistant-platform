# 数据库设计 V1

> 依据：[AI智能助手平台_Phase0_系统设计_V1.md](../plan/AI智能助手平台_Phase0_系统设计_V1.md)  
> 决议：[v2-planning-review.md](../plan/v2-planning-review.md) R1–R6
> 可执行脚本：[mysql/ddl_v1.sql](./mysql/ddl_v1.sql)  
> 种子数据：[mysql/seed_v1.sql](./mysql/seed_v1.sql)

---

## 1. 约定

| 项 | 约定 |
|---|---|
| 引擎 | InnoDB |
| 字符集 | `utf8mb4` / `utf8mb4_unicode_ci` |
| 主键 | `CHAR(36)` UUID 字符串 |
| 时间 | `DATETIME(3)`，应用层写 UTC 或统一时区 |
| 软删 | 业务表用 `status`（如 `DELETED`），审计表不物理删历史 |
| 真源 | `document_chunk.content` = Chunk 全文；Qdrant 不含正文；文件在 FileStorage |

---

## 2. ER 关系（一期）

```text
organization
  ├── sys_user / sys_role
  ├── space (含 is_default=1 的 Default Space)
  ├── platform_ai_config (org 级 Embedding)
  └── knowledge_base
        ├── rag_config (1:1)
        ├── knowledge_base_member
        └── document
              ├── document_chunk
              └── document_job

conversation → conversation_message → message_citation
audit_log
```

---

## 3. 关键唯一约束

| 表 | 约束 | 含义 |
|---|---|---|
| `sys_user` | `uk_user_org_username (org_id, username)` | 同组织用户名唯一 |
| `sys_role` | `uk_role_org_code (org_id, code)` | 同组织角色码唯一 |
| `sys_permission` | `uk_permission_code (code)` | 权限码全局唯一 |
| `organization` | `uk_org_code (code)` | 组织编码唯一 |
| `sys_user_role` | `uk_user_role (user_id, role_id)` | |
| `sys_role_permission` | `uk_role_permission (role_id, permission_id)` | |
| `space_member` | `uk_space_member (space_id, user_id)` | |
| `knowledge_base_member` | `uk_kb_member (kb_id, user_id)` | |
| `rag_config` | `uk_rag_config_kb (kb_id)` | 每 KB 一份配置 |
| `document` | `uk_document_kb_hash (kb_id, file_hash)` | 同 KB SHA-256 去重 |
| `document_chunk` | `uk_chunk_doc_index (document_id, chunk_index)` | |
| `platform_ai_config` | 应用保证每 org 至多一条 `is_active=1` | 见种子与服务逻辑 |

Default Space：每 org 至少一个 `is_default=1`；由创建组织事务保证（见种子脚本）。MySQL 对「仅 default 唯一」用生成列约束：

```text
uk_space_org_default_key：仅当 is_default=1 时写入 org_id，否则 NULL（多 NULL 不冲突）
```

---

## 4. 枚举（VARCHAR 存储，应用层校验）

| 字段 | 取值 |
|---|---|
| `sys_user.status` / `organization.status` / `sys_role.status` | `ACTIVE` / `DISABLED` |
| `sys_permission.type` | `MENU` / `BUTTON` / `API` |
| `space_member.role` | `OWNER` / `MEMBER` |
| `knowledge_base.visibility` | `PRIVATE` / `SPACE` |
| `knowledge_base.status` | `ACTIVE` / `ARCHIVED` |
| `knowledge_base_member.role` | `OWNER` / `EDITOR` / `VIEWER` |
| `document.status` | `UPLOADED` / `PROCESSING` / `READY` / `FAILED` / `DELETED` |
| `document_job.status` | `PENDING` / `PARSING` / `CHUNKING` / `EMBEDDING` / `INDEXING` / `SUCCESS` / `FAILED` / `CANCELLED` |
| `document_job.job_type` | `PARSE_INDEX` / `REINDEX`（可扩展） |
| `conversation_message.role` | `USER` / `ASSISTANT` / `SYSTEM` |
| `conversation_message.status` | `GENERATING` / `COMPLETED` / `ABORTED` / `FAILED` |
| `audit_log.result` | `SUCCESS` / `DENIED` / `FAILED` |

---

## 5. 与向量库的边界

```text
删除文档（逻辑）：
  1) Qdrant delete_by_document(document_id)
  2) DELETE document_chunk WHERE document_id = ?
  3) document.status = DELETED

重建索引：
  读 MySQL document_chunk → 平台 Embedding → 写 Qdrant
  不依赖 Qdrant payload 中的正文
```

---

## 6. 种子数据说明

`seed_v1.sql` 提供本地开发最小集：

- 1 个 `organization`（`demo`）
- 1 个 Default Space
- `ADMIN` / `USER` 角色 + 基础 permission
- 管理员用户（密码 hash 占位，脚手架时替换为真实 bcrypt）
- 1 条 `platform_ai_config`（dimension 与部署模型对齐后再改）

---

## 7. 下一步

1. 本地：`mysql < docs/mysql/ddl_v1.sql && mysql < docs/mysql/seed_v1.sql`
2. 后续：Alembic 将本 DDL 收敛为初始 migration（与 SQLAlchemy models 对齐）
3. 并行：OpenAPI Schema + Error Matrix 细化
