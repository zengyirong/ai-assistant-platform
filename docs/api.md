# API V1 设计

> 依据：Phase 0 §8 / Error Matrix / RBAC  
> OpenAPI：[`openapi-v1.yaml`](./openapi-v1.yaml)  
> SSE：[`sse-protocol.md`](./sse-protocol.md)  
> 原则：**OpenAPI ≠ API 设计**；本文 + Error Matrix 为一等契约，Pydantic 生成 OpenAPI 时必须与之对齐。

---

## 1. 约定

| 项 | 约定 |
|---|---|
| 业务前缀 | `/api/v1` |
| 基础设施 | `/health`、`/ready`（不走 v1） |
| 鉴权 | `Authorization: Bearer <jwt>`（login 除外） |
| 成功包 | `{ "code": "OK", "message": "success", "data": ..., "request_id": "..." }` |
| 错误包 | `{ "code": "<ERROR_CODE>", "message": "...", "request_id": "...", "details": optional }` |
| 分页 | `page`（从 1）、`page_size`（默认 20，最大 100）；列表 `data: { items, total, page, page_size }` |
| ID | UUID 字符串 |
| 上传 | `multipart/form-data`；单文件 ≤ 20MB；`pdf` / `docx` / `txt` |
| 流式 | `POST /api/v1/chat/stream` → `text/event-stream`（见 SSE 文档） |

前端业务判断依赖 **`code`**，不依赖 `message` 字符串。

---

## 2. Error Matrix

| HTTP | Code | 场景 | 典型路由 |
| ---: | --- | --- | --- |
| 400 | `VALIDATION_ERROR` | 参数 / Body / Query 不合法 | 全局 |
| 401 | `AUTH_UNAUTHORIZED` | 未登录、Token 无效或过期 | 需鉴权接口 |
| 403 | `PERMISSION_DENIED` | 功能权限不足（menu/button/API） | 写操作等 |
| 403 | `KB_PERMISSION_DENIED` | 无该 KB 数据权限 | KB / Document / Chat |
| 404 | `KB_NOT_FOUND` | 知识库不存在或不可见 | KB / Document |
| 404 | `DOCUMENT_NOT_FOUND` | 文档不存在 | Document |
| 404 | `SPACE_NOT_FOUND` | 空间不存在 | Space |
| 404 | `CONVERSATION_NOT_FOUND` | 会话不存在或不属于当前用户 | Conversation |
| 409 | `DOCUMENT_DUPLICATED` | 同 KB 内 `file_hash` 冲突 | Upload |
| 409 | `SPACE_NAME_CONFLICT` | 同 org 下空间名冲突（可选） | Space create/update |
| 409 | `USER_NAME_CONFLICT` | 用户名已存在 | User create |
| 422 | `DOCUMENT_FORMAT_INVALID` | 扩展名 / MIME 不在白名单 | Upload |
| 422 | `DOCUMENT_TOO_LARGE` | 超过大小限制 | Upload |
| 422 | `DOCUMENT_PARSE_FAILED` | 解析任务失败（查询 job 或 retry 结果） | Document / Job |
| 429 | `LLM_RATE_LIMIT` | 上游模型限流 | Chat |
| 503 | `VECTOR_STORE_UNAVAILABLE` | Qdrant 不可用 | Chat / Indexing |
| 503 | `SERVICE_UNAVAILABLE` | ready 依赖未就绪 | `/ready` |
| 504 | `LLM_TIMEOUT` | LLM 超时 | Chat |
| 500 | `INTERNAL_ERROR` | 未预期异常 | 全局 |
| — | `SSE_CLIENT_ABORTED` | 客户端断开（写入 message 状态 / 审计，不一定作为 HTTP 响应体） | Chat stream |

SSE 路径上的业务错误通过 `event: error` 下发，`data.code` 使用上表同一套 Code。

---

## 3. 路由鉴权矩阵

图例：`JWT` = 需登录；`Perm` = 功能权限码；`Data` = 额外数据权限检查。

| Method | Path | JWT | Perm | Data |
|---|---|---|---|---|
| GET | `/health` | 否 | — | — |
| GET | `/ready` | 否 | — | — |
| POST | `/api/v1/auth/login` | 否 | — | — |
| POST | `/api/v1/auth/logout` | 是 | — | — |
| GET | `/api/v1/auth/me` | 是 | — | — |
| GET | `/api/v1/users` | 是 | — | 本 org ACTIVE 用户（`q` 搜 username/nickname） |
| POST | `/api/v1/users` | 是 | — | **ADMIN**；同 org 创建 `USER`（薄接口，非完整用户管理） |
| GET | `/api/v1/audit-logs` | 是 | — | **ADMIN**；本 org；可选 `action` / `user_id` |
| GET | `/api/v1/spaces` | 是 | — | 本 org 可见 space |
| POST | `/api/v1/spaces` | 是 | — | 本 org |
| GET | `/api/v1/spaces/{id}` | 是 | — | 成员或 ADMIN |
| PUT | `/api/v1/spaces/{id}` | 是 | — | OWNER / ADMIN |
| DELETE | `/api/v1/spaces/{id}` | 是 | — | OWNER / ADMIN；**禁止删 Default Space** |
| GET/POST/DELETE | `/api/v1/spaces/{id}/members...` | 是 | — | OWNER / ADMIN |
| GET | `/api/v1/knowledge-bases` | 是 | `knowledge:list` | 可访问 KB 过滤 |
| POST | `/api/v1/knowledge-bases` | 是 | `knowledge:create` | — |
| GET | `/api/v1/knowledge-bases/{id}` | 是 | `knowledge:list` | KB 数据权限 |
| PUT | `/api/v1/knowledge-bases/{id}` | 是 | `knowledge:update` | OWNER/EDITOR 或 ADMIN |
| DELETE | `/api/v1/knowledge-bases/{id}` | 是 | `knowledge:delete` | OWNER 或 ADMIN |
| * | `/api/v1/knowledge-bases/{id}/members...` | 是 | `knowledge:update` | OWNER 或 ADMIN |
| GET/PUT | `/api/v1/knowledge-bases/{id}/rag-config` | 是 | list / update | KB 数据权限 |
| GET | `/api/v1/knowledge-bases/{kb_id}/documents` | 是 | `document:list` | KB 数据权限 |
| POST | `/api/v1/knowledge-bases/{kb_id}/documents` | 是 | `document:upload` | KB 写权限 |
| GET | `/api/v1/documents/{id}` | 是 | `document:list` | 所属 KB 权限 |
| DELETE | `/api/v1/documents/{id}` | 是 | `document:delete` | KB 写权限 |
| POST | `/api/v1/documents/{id}/retry` | 是 | `document:retry` | KB 写权限 |
| GET | `/api/v1/documents/{id}/jobs` | 是 | `document:list` | 所属 KB 权限 |
| GET/POST/... | `/api/v1/conversations...` | 是 | `conversation:*` | **仅本人会话**（ADMIN 可看本 org 可选，一期默认仅本人） |
| POST | `/api/v1/chat/stream` | 是 | `conversation:create` 或等价 chat 权限 | 每个 `kb_ids` 均需可访问 |

KB 数据权限（USER）：

```text
PRIVATE KB：创建者或 KB Member
SPACE KB：该 Space 成员，或 KB Member
ADMIN：当前 org 全部
```

---

## 4. 端点摘要

### 4.1 Auth

**POST `/api/v1/auth/login`**

```json
// request
{ "username": "admin", "password": "..." }

// data
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { "id", "username", "nickname", "org_id", "roles": ["ADMIN"] }
}
```

**GET `/api/v1/auth/me`** → 当前用户 + roles + permissions（codes 列表）。

**POST `/api/v1/auth/logout`** → 一期可无服务端黑名单，返回 OK（前端丢弃 token）；预留审计。

### 4.1.1 Users（组织内用户，供成员选择器）

**GET `/api/v1/users?q=&page=&page_size=`**

- 仅返回当前登录用户所在 org 的 `ACTIVE` 用户
- `q` 可选，匹配 `username` / `nickname`（模糊）
- `data.items[]`: `{ id, username, nickname, status }`

**POST `/api/v1/users`**（ADMIN）

```json
// request
{ "username": "alice", "password": "User@123456", "nickname": "Alice" }

// data
{ "id", "username", "nickname", "status": "ACTIVE" }
```

- 仅 `ADMIN`；新用户归属当前 org，绑定 `USER` 角色
- 用户名：3–32 位字母/数字/下划线；一期登录按全局用户名查找，故全局唯一
- 冲突：`USER_NAME_CONFLICT`（409）
- 审计：`user.create`

### 4.1.2 Audit Logs（ADMIN）

**GET `/api/v1/audit-logs?page=&page_size=&action=&user_id=`**

- 仅 `ADMIN`；限定当前 org
- 写入动作（best-effort，失败不阻断业务）：`auth.login` / `auth.logout` / `document.upload` / `document.delete` / `document.retry` / `kb.member.upsert` / `kb.member.remove` / `user.create`
- `result`: `SUCCESS` / `FAILED` / `DENIED`
- `data.items[]`: `{ id, org_id, user_id, action, resource_type, resource_id, request_id, result, ip, user_agent, detail, created_at }`

### 4.2 Space

| 操作 | 说明 |
|---|---|
| list/create/get/update/delete | 一期必要 CRUD |
| members | add / remove；role = `OWNER` \| `MEMBER` |
| delete default | 返回 `VALIDATION_ERROR` 或 `PERMISSION_DENIED` |

Create body：`{ "name", "description?" }` — 归属当前用户 `org_id`。

### 4.3 Knowledge Base

Create：

```json
{
  "name": "员工手册",
  "description": "",
  "visibility": "PRIVATE",
  "space_id": null
}
```

- `PRIVATE`：`space_id` 可空  
- `SPACE`：`space_id` 必填（通常 Default Space 或所选 Space）

创建成功后自动：创建者 `OWNER` member + 默认 `rag_config`。

### 4.4 RAG Config

GET/PUT `/knowledge-bases/{id}/rag-config`

Body（无 `embedding_model`）：

```json
{
  "chunk_strategy": "recursive",
  "chunk_size": 800,
  "chunk_overlap": 120,
  "top_k": 5,
  "score_threshold": null,
  "llm_model": null,
  "temperature": 0.2,
  "system_prompt": null
}
```

### 4.5 Document

**POST** multipart：字段 `file`。

成功 `data`：

```json
{
  "id": "doc_...",
  "kb_id": "...",
  "file_name": "手册.pdf",
  "file_hash": "...",
  "file_type": "pdf",
  "file_size": 12345,
  "status": "UPLOADED",
  "job_id": "job_..."
}
```

重复：`409 DOCUMENT_DUPLICATED`。

**DELETE**：逻辑删 + 清 Qdrant + 删 `document_chunk`（顺序见 database.md）。

**retry**：对 `FAILED` 文档新建或重置 job。

### 4.6 Conversation

Create：`{ "title?", "kb_ids?" }` → 写入 `kb_scope` JSON。

Messages：按时间升序；含 `citations[]`（assistant 消息）。

### 4.7 Chat Stream

**POST `/api/v1/chat/stream`**

```json
{
  "conversation_id": "conv_x",
  "question": "...",
  "kb_ids": ["kb_1", "kb_2"]
}
```

- `kb_ids` 空：在用户可访问 KB 全集内检索（仍 Global Top-K）  
- 任一无权 → `403 KB_PERMISSION_DENIED`（流开始前 HTTP 错误，或首包前失败；推荐 **流建立前校验**，失败走普通 JSON 错误）  
- 成功：`200` + `text/event-stream`  
- Abort：客户端断开；`message.status = ABORTED`；无独立 abort HTTP API

---

## 5. 资源 DTO（逻辑字段）

与 DDL 对齐的响应字段（蛇形命名，JSON）：

- **User**：`id, org_id, username, nickname, email, status, roles[], permissions[]`
- **Space**：`id, org_id, name, description, is_default, owner_id, created_at, updated_at`
- **KnowledgeBase**：`id, org_id, space_id, name, description, visibility, status, created_by, document_count?, created_at, updated_at`
- **Document**：`id, org_id, kb_id, file_name, file_hash, file_type, file_size, page_count, status, created_by, created_at, updated_at`
- **DocumentJob**：`id, document_id, job_type, status, progress, retry_count, error_code, error_message, started_at, finished_at`
- **Conversation**：`id, org_id, user_id, title, kb_scope, created_at, updated_at`
- **Message**：`id, conversation_id, role, content, status, request_id, citations[], created_at`
- **Citation**：`document_id, document_name?, chunk_id, page, section, score, snippet, sort_order`

---

## 6. 实现提示

1. 统一异常 → `code` + HTTP 映射中间件。  
2. 每个请求生成 `request_id`（网关或中间件），写入日志 / 审计 / SSE。  
3. Chat 流：先鉴权与 KB 校验，再落 USER message + ASSISTANT(`GENERATING`)，再 SSE。  
4. OpenAPI 由 FastAPI 生成后，对照本文回归；以本文 Error Matrix 为准修正。

---

## 7. 下一步

- [x] 本文 + Error / 鉴权矩阵  
- [x] `openapi-v1.yaml` 骨架  
- [ ] FastAPI Router + Pydantic 落地时与 YAML 双向校验  
- [ ] docker-compose + 后端脚手架  
