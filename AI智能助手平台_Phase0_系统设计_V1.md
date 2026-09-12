# AI 智能助手平台 — Phase 0 系统设计 V1

> 阶段：Phase 0 / Design  
> 范围：一期「文档 RAG 智能查询助手」  
> 前端：Vben Admin 5 + Vue3 + TypeScript + Element Plus + Pinia  
> 后端：Python + FastAPI + SQLAlchemy 2 + MySQL 8  
> AI：LangChain + OpenAI Compatible API  
> 向量库：Qdrant（一期推荐）  
> 部署：Docker Compose  
> 修订：2026-09-12 — 对齐审查 R1–R6 拍板（`document_chunk` 真源、平台级 Embedding、Default Space、Error Matrix、ADR-008）

---

# 1. Phase 0 目标

Phase 0 不直接实现业务功能，而是先固定：

1. 系统上下文与模块边界
2. 模块依赖方向
3. MySQL / Qdrant 数据职责
4. RBAC 与知识库检索权限
5. 文档处理状态机
6. API V1 草案
7. SSE V1 协议
8. 前后端目录结构
9. Docker 基础依赖
10. 关键架构决策（ADR）

完成后再进入 Phase 1 基础平台编码。


# 2. 系统上下文

```text
┌─────────────────────────────────────────────┐
│               管理员 / 普通用户             │
└─────────────────────┬───────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────┐
│              Vben Admin 5 Frontend          │
│ 登录 / RBAC / 知识库 / 文档 / Chat / 引用   │
└─────────────────────┬───────────────────────┘
                      │ REST + SSE
                      ▼
┌─────────────────────────────────────────────┐
│                FastAPI Backend              │
│ Auth / RBAC / Knowledge / Document / Chat   │
│ Job / Audit / AI Orchestration              │
└───────┬──────────────┬──────────────┬───────┘
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│   MySQL 8    │ │    Qdrant    │ │ LLM / Embedding  │
│ 业务 + Chunk │ │ 向量索引     │ │ Compatible API   │
│ 全文真源      │ │ (无正文)     │ │ 平台级统一模型    │
└──────────────┘ └──────────────┘ └──────────────────┘
        │
        ▼
┌──────────────────┐
│ Local FileStorage│
│ 原始文档真源      │
│ future: MinIO/S3 │
└──────────────────┘
```


# 3. 核心业务流

## 3.1 文档上传与索引

```text
Upload
  ↓
Permission Check
  ↓
File Validation
  ↓
SHA-256(raw bytes) → 同 KB 内 kb_id+file_hash 去重
  ↓
Save Original File（FileStorage = 原始文档真源）
  ↓
Create document
  ↓
Create document_job
  ↓
PENDING
  ↓
PARSING
  ↓
CHUNKING → 写入 MySQL document_chunk（全文真源）
  ↓
EMBEDDING（平台级 Embedding Config）
  ↓
INDEXING → 写入 Qdrant（仅向量 + 过滤字段）
  ↓
SUCCESS
```

失败时：

```text
FAILED
  ↓
保存 error_code / error_message
  ↓
用户 Retry
```

去重：

```text
同 KB + 相同 file_hash → DOCUMENT_DUPLICATED (409)
跨 KB + 相同文件 → 允许各自索引
```

## 3.2 RAG 问答

```text
Question
  ↓
Auth
  ↓
计算可访问 KB IDs
  ↓
Query Embedding（平台级同一模型）
  ↓
一次 Qdrant Search
  filter: org_id + kb_id IN (...)
  limit: Global Top-K
  ↓
返回 chunk_id[] + score
  ↓
MySQL 批量查询 document_chunk（取全文）
  ↓
Score Threshold
  ↓
Prompt Builder
  ↓
LLM Stream
  ↓
SSE text / citation / done
```

**原则：权限过滤必须发生在 Retriever / Vector Search 阶段，而不是检索后让 LLM 判断。**

**原则：多 KB 不做「每 KB 各查 top_k 再 merge」，由 Qdrant 在候选集合上直接 Global Top-K。**


# 4. 分层与模块

```text
API Layer
   ↓
Application / Service Layer
   ↓
Repository / AI Interface
   ↓
Infrastructure
```

核心模块：

```text
core/
├── auth
├── rbac
├── organization
├── audit
├── config
├── errors
└── logging

modules/
├── knowledge
├── document
├── conversation
└── job

ai/
├── llm
├── embedding
├── parser
├── chunker
├── retrieval
├── prompt
├── citation
└── vectorstore

domains/
├── hospital
└── hr
```

允许：

```text
API → Service → Repository / AI Interface → Infrastructure
Domain → Modules → AI
```

禁止：

```text
Router → SQL
Router → Qdrant
HR → Qdrant Client
Hospital → OpenAI SDK
Service → 未抽象的具体 AI Provider
```


# 5. 核心数据模型

一期核心表：

```text
sys_user
sys_role
sys_permission
sys_user_role
sys_role_permission

organization
space
space_member

platform_ai_config

knowledge_base
knowledge_base_member
rag_config

document
document_chunk
document_job

conversation
conversation_message
message_citation

audit_log
```

ER 草案：

```text
organization
    │
    ├──< sys_user
    ├──1 default space（创建组织时自动创建）
    ├──< space
    ├──1 platform_ai_config（平台级 Embedding）
    └──< knowledge_base

sys_user
    ├──< sys_user_role >── sys_role
    ├──< space_member >── space
    ├──< knowledge_base_member >── knowledge_base
    └──< conversation

knowledge_base
    ├──1 rag_config
    ├──< document
    └──< document_chunk

document
    ├──< document_chunk
    └──< document_job

conversation
    └──< conversation_message
              └──< message_citation
```

真源职责：

```text
MySQL document_chunk  = Chunk 内容真源
Qdrant                = 向量搜索索引（不含全文）
FileStorage           = 原始文档真源
```


# 6. 表结构草案

## sys_user

```text
id
org_id
username
password_hash
nickname
email
status
created_at
updated_at
```

## sys_role

```text
id
org_id
code
name
status
created_at
updated_at
```

默认角色：

```text
ADMIN
USER
```

## sys_permission

```text
id
code
name
type
parent_id
created_at
```

type：

```text
MENU
BUTTON
API
```

## organization

```text
id
name
code
status
created_at
updated_at
```

创建组织时必须自动创建 **Default Space**（名称如「默认空间」），并将创建者加入为成员。

一期不做完整 Organization 管理 API；org 由种子数据 / 登录上下文绑定。

## space

```text
id
org_id
name
description
is_default
owner_id
created_at
updated_at
```

一期约束：

- 每个 org 至少一个 Default Space（`is_default = true`）
- Space API 只保留：列表 / 详情 / 创建 / 修改 / 成员管理
- 不做：部门树、嵌套、权限继承、配额、Owner 转移流程

## space_member

```text
id
space_id
user_id
role
created_at
```

role（一期简化）：

```text
OWNER
MEMBER
```

## sys_user_role

```text
id
user_id
role_id
created_at
```

唯一约束：`user_id + role_id`

## sys_role_permission

```text
id
role_id
permission_id
created_at
```

唯一约束：`role_id + permission_id`

## platform_ai_config

平台级 AI / Embedding 配置（**一期全局唯一有效配置**，禁止每 KB 自选 embedding）：

```text
id
org_id
embedding_provider
embedding_model
embedding_dimension
is_active
created_at
updated_at
```

说明：

- 统一 `knowledge_chunks` collection + 多 KB 一次检索，要求同一 Embedding 空间与维度
- 不同 KB 若使用不同 dimension 的 embedding_model，无法在同一向量空间做 Global Top-K

## knowledge_base

```text
id
org_id
space_id
name
description
visibility
status
created_by
created_at
updated_at
```

visibility：

```text
PRIVATE
SPACE
```

## knowledge_base_member

```text
id
kb_id
user_id
role
created_at
```

role：

```text
OWNER
EDITOR
VIEWER
```

唯一约束：`kb_id + user_id`

## rag_config

KB 级检索 / 生成参数（**不含** embedding_model）：

```text
id
kb_id
chunk_strategy
chunk_size
chunk_overlap
top_k
score_threshold
llm_model
temperature
system_prompt
created_at
updated_at
```

## document

```text
id
org_id
kb_id
file_name
storage_path
file_hash
file_type
file_size
page_count
status
created_by
created_at
updated_at
```

`file_hash`：`SHA-256(raw file bytes)`  
唯一约束：**`kb_id + file_hash`**（同 KB 去重；跨 KB 允许）

status：

```text
UPLOADED
PROCESSING
READY
FAILED
DELETED
```

## document_chunk

Chunk 内容真源（MySQL）：

```text
id
org_id
kb_id
document_id
chunk_index
content
content_hash
page
section
token_count
created_at
updated_at
```

唯一约束：`document_id + chunk_index`  
索引建议：`kb_id`、`document_id`、`content_hash`

## document_job

```text
id
document_id
job_type
status
progress
retry_count
error_code
error_message
started_at
finished_at
created_at
updated_at
```

status：

```text
PENDING
PARSING
CHUNKING
EMBEDDING
INDEXING
SUCCESS
FAILED
CANCELLED
```

## conversation

```text
id
org_id
user_id
title
kb_scope
created_at
updated_at
```

一期 `kb_scope` 可暂存 JSON，后续需要复杂查询时再拆关系表。

## conversation_message

```text
id
conversation_id
role
content
status
request_id
token_input
token_output
created_at
updated_at
```

role：

```text
USER
ASSISTANT
SYSTEM
```

status：

```text
GENERATING
COMPLETED
ABORTED
FAILED
```

## message_citation

```text
id
message_id
document_id
chunk_id
page
section
score
snippet
sort_order
created_at
```

## audit_log

```text
id
org_id
user_id
action
resource_type
resource_id
request_id
result
ip
user_agent
detail
created_at
```


# 7. Qdrant 设计

一期推荐统一 collection：

```text
knowledge_chunks
```

不采用“一知识库一个 collection”。

前提：全平台（至少同一 org）使用 **同一 Embedding 模型与维度**（见 `platform_ai_config`）。

Payload（**不含 content 全文**）：

```json
{
  "org_id": "org_x",
  "kb_id": "kb_x",
  "document_id": "doc_x",
  "chunk_id": "chunk_x",
  "page": 12,
  "section": "请假制度"
}
```

Retriever：

```text
Qdrant Search
  filter: org_id == current_org AND kb_id IN accessible_kb_ids
  limit: Global Top-K
        ↓
返回 chunk_id[] + score
        ↓
MySQL IN (chunk_id) 批量取 document_chunk.content
```

这样可以控制 collection 数量，并自然承载 `org_id / kb_id` 数据权限；换向量库 / 重建索引 / Citation / RAG Eval 均不依赖 Qdrant 存正文。


# 8. API V1 草案

统一前缀：

```text
/api/v1
```

## Auth

```text
POST /auth/login
POST /auth/logout
GET  /auth/me
```

## Space

一期收敛范围：列表 / 详情 / 创建 / 修改 / 成员管理。  
不做嵌套、配额、权限继承、Owner 转移。创建组织时自动有 Default Space。

```text
GET    /spaces
POST   /spaces
GET    /spaces/{id}
PUT    /spaces/{id}
DELETE /spaces/{id}
GET    /spaces/{id}/members
POST   /spaces/{id}/members
DELETE /spaces/{id}/members/{user_id}
```

## Knowledge Base

```text
GET    /knowledge-bases
POST   /knowledge-bases
GET    /knowledge-bases/{id}
PUT    /knowledge-bases/{id}
DELETE /knowledge-bases/{id}

GET    /knowledge-bases/{id}/members
POST   /knowledge-bases/{id}/members
DELETE /knowledge-bases/{id}/members/{user_id}

GET    /knowledge-bases/{id}/rag-config
PUT    /knowledge-bases/{id}/rag-config
```

## Document

```text
GET    /knowledge-bases/{kb_id}/documents
POST   /knowledge-bases/{kb_id}/documents
GET    /documents/{id}
DELETE /documents/{id}
POST   /documents/{id}/retry
GET    /documents/{id}/jobs
```

## Conversation

```text
GET    /conversations
POST   /conversations
GET    /conversations/{id}
DELETE /conversations/{id}
GET    /conversations/{id}/messages
```

## Chat

```text
POST /chat/stream
```

请求：

```json
{
  "conversation_id": "conv_x",
  "question": "公司的年假政策是什么？",
  "kb_ids": ["kb_1"]
}
```

普通响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": {},
  "request_id": "req_xxx"
}
```

错误响应：

```json
{
  "code": "KB_PERMISSION_DENIED",
  "message": "无权访问该知识库",
  "request_id": "req_xxx"
}
```

## Error Matrix（一期基线）

Pydantic Schema 生成 OpenAPI，但 **OpenAPI ≠ API 设计**。错误码矩阵须手工维护为一等契约。

| HTTP | Code | 场景 |
| ---: | --- | --- |
| 400 | `VALIDATION_ERROR` | 参数错误 |
| 401 | `AUTH_UNAUTHORIZED` | 未登录 / Token 无效 |
| 403 | `PERMISSION_DENIED` | 功能权限不足 |
| 403 | `KB_PERMISSION_DENIED` | 无 KB 数据权限 |
| 404 | `KB_NOT_FOUND` | KB 不存在 |
| 404 | `DOCUMENT_NOT_FOUND` | 文档不存在 |
| 409 | `DOCUMENT_DUPLICATED` | KB 内重复文件（`kb_id+file_hash`） |
| 422 | `DOCUMENT_PARSE_FAILED` | 文档不可解析 |
| 429 | `LLM_RATE_LIMIT` | 模型限流 |
| 503 | `VECTOR_STORE_UNAVAILABLE` | Qdrant 不可用 |
| 504 | `LLM_TIMEOUT` | LLM 超时 |
| 500 | `INTERNAL_ERROR` | 未预期异常 |

基础设施接口（**不**走 `/api/v1`）：

```text
GET /health
GET /ready
```


# 9. SSE Protocol V1

统一数据结构：

```json
{
  "version": "1.0",
  "event": "text",
  "request_id": "req_xxx",
  "conversation_id": "conv_xxx",
  "message_id": "msg_xxx",
  "seq": 2,
  "data": {}
}
```

一期事件：

```text
start
text
citation
done
error
```

`citation` 示例：

```json
{
  "version": "1.0",
  "event": "citation",
  "request_id": "req_1",
  "conversation_id": "conv_1",
  "message_id": "msg_1",
  "seq": 8,
  "data": {
    "citations": [
      {
        "document_id": "doc_1",
        "document_name": "员工手册.pdf",
        "chunk_id": "chunk_12",
        "page": 12,
        "section": "年假制度",
        "score": 0.86,
        "snippet": "..."
      }
    ]
  }
}
```

协议规则：

1. `seq` 严格单调递增。
2. `error` 后不能再发送 `done`。
3. `done` 后不能再发送任何业务事件。
4. 未识别的新 `event` 前端忽略，保证向前兼容。
5. `request_id` 贯穿 API、日志、审计和 SSE。


# 10. Abort 设计

```text
用户点击停止
   ↓
AbortController.abort()
   ↓
连接断开
   ↓
FastAPI 感知 disconnect
   ↓
尽力停止上游模型 stream
   ↓
message.status = ABORTED
```

禁止：

```text
ABORTED → COMPLETED
```


# 11. 前端目录建议

```text
apps/web-ele/src/
├── api/
│   ├── auth/
│   ├── knowledge/
│   ├── document/
│   ├── conversation/
│   └── system/
│
├── views/
│   ├── system/
│   ├── knowledge/
│   ├── document/
│   └── ai-chat/
│
├── components/
│   └── ai/
│       ├── ChatMessage/
│       ├── ChatInput/
│       ├── CitationDrawer/
│       ├── SourceCard/
│       └── StreamingText/
│
├── composables/
│   ├── useSseChat.ts
│   ├── useAbortChat.ts
│   └── useCitation.ts
│
├── stores/
│   ├── conversation.ts
│   └── knowledge.ts
│
└── types/
    ├── knowledge.ts
    ├── document.ts
    ├── conversation.ts
    └── sse.ts
```

职责：

```text
Vben → Layout / Router / RBAC / Tabs
Element Plus → 普通业务 UI
VXE Table → 后期复杂表格
自研 AI Components → Chat / Citation / Streaming
```


# 12. 后端目录建议

```text
backend/
├── app/
│   ├── api/v1/
│   ├── core/
│   │   ├── auth/
│   │   ├── rbac/
│   │   ├── audit/
│   │   ├── config.py
│   │   ├── errors.py
│   │   └── logging.py
│   ├── modules/
│   │   ├── knowledge/
│   │   ├── document/
│   │   ├── conversation/
│   │   └── job/
│   ├── ai/
│   │   ├── llm/
│   │   ├── embedding/
│   │   ├── parser/
│   │   ├── chunker/
│   │   ├── retrieval/
│   │   ├── prompt/
│   │   ├── citation/
│   │   └── vectorstore/
│   ├── domains/
│   │   ├── hospital/
│   │   └── hr/
│   ├── repositories/
│   ├── models/
│   ├── schemas/
│   ├── db/
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   └── rag_eval/
├── alembic/
├── pyproject.toml
└── Dockerfile
```

一期 `hospital`、`hr` 不写具体业务代码。


# 13. 核心抽象

```python
class VectorStore:
    async def add_chunks(self, chunks): ...
    async def delete_by_document(self, document_id: str): ...
    async def search(self, query_vector, filters, top_k: int): ...

class EmbeddingClient:
    async def embed_documents(self, texts: list[str]): ...
    async def embed_query(self, query: str): ...

class LLMClient:
    async def invoke(self, messages): ...
    async def stream(self, messages): ...

class FileStorage:
    async def save(self, file): ...
    async def delete(self, path: str): ...
```

目的：

- 隔离 LangChain 和模型 SDK
- 可替换 Provider
- 可替换 Qdrant / 其他向量库
- 方便 Mock 与自动化测试


# 14. Docker Compose 基线

一期核心服务：

```text
mysql
qdrant
backend
frontend
```

开发阶段推荐先只容器化：

```text
mysql
qdrant
```

前后端本机启动，提高调试效率。

未来加入：

```text
redis
worker
minio
```

Backend 必须提供（基础设施，不属于业务 API）：

```text
GET /health
GET /ready
```

不挂在 `/api/v1` 下。


# 15. 环境变量

```text
APP_ENV
APP_SECRET

MYSQL_HOST
MYSQL_PORT
MYSQL_DATABASE
MYSQL_USER
MYSQL_PASSWORD

QDRANT_URL
QDRANT_API_KEY

LLM_BASE_URL
LLM_API_KEY
LLM_MODEL

EMBEDDING_BASE_URL
EMBEDDING_API_KEY
EMBEDDING_MODEL
EMBEDDING_DIMENSION

FILE_STORAGE_PATH
MAX_UPLOAD_SIZE_MB=20
```

要求：

- `.env` 不提交 Git
- 提供 `.env.example`
- 模型 API Key 仅存在服务端


# 16. RBAC 基线

角色：

```text
ADMIN
USER
```

权限示例：

```text
knowledge:list
knowledge:create
knowledge:update
knowledge:delete

document:list
document:upload
document:delete
document:retry

conversation:list
conversation:create
conversation:delete
```

数据权限：

```text
ADMIN
  → 当前 org 全部数据

USER
  → 自己的 Private KB
  + 已加入的 Space KB
  + KnowledgeBase Member
```


# 17. RAG 默认参数基线

平台级 Embedding（`platform_ai_config` / 环境变量）：

```text
embedding_provider = openai_compatible
embedding_model    = （部署时选定，全平台统一）
embedding_dimension = （与模型一致）
```

KB 级 `rag_config`：

```text
chunk_strategy = recursive
chunk_size = 800
chunk_overlap = 120
top_k = 5
temperature = 0.2
```

多 KB 检索：

```text
一次 Qdrant Search
+ kb_id IN (...)
+ Global Top-K = top_k
```

禁止：

```text
每 KB 各查 top_k → 再应用层 merge
每 KB 自选 embedding_model
```

文件：

```text
hash = SHA-256(raw file bytes)
去重 = UNIQUE(kb_id, file_hash)
上传上限 = 20MB
格式 = PDF / DOCX / TXT
```

`score_threshold` 不在设计阶段写死统一数值。

原因：

- 不同 Embedding 模型不同
- 不同 distance metric 不同
- 不同 Vector DB 分数语义不同

最终通过 Golden Dataset 校准。

拒答：

```text
0 chunks
OR
all chunks below threshold
        ↓
当前知识库中未找到可靠依据。
```


# 18. 测试架构

## 18.1 分层

```text
Unit
├── RBAC
├── Chunker
├── Citation Builder
├── Prompt Builder
└── Hash

Integration
├── Upload → document_chunk → Vector
├── Delete → Vector Cleanup + MySQL chunk
├── Retry
└── Permission + Retriever

API
├── Auth
├── KB
├── Document
└── Conversation

SSE
├── Event Order
├── seq
├── error
└── abort

RAG Eval
└── Golden Dataset
```

## 18.2 节奏（ADR-008）

测试与功能同步开发（Shift Left），**禁止**最后集中补测试。

```text
实现功能
   ↓
Unit Test
   ↓
Integration / API Test
   ↓
Lint + Type Check
   ↓
PR
```

示例：实现 Document Upload 的同一任务须包含上传 Service、文件类型/大小/Hash/权限测试、Upload API Test。

DoD：

```text
代码 ≠ 完成
代码 + 测试 + 权限 + 异常 + 日志 + 文档 = Done
```

## 18.3 质量门禁工具

```text
Frontend
ESLint / Prettier / Stylelint / vue-tsc / Vitest

Backend
Ruff / Black / mypy / Pytest
```


# 19. ADR — 已拍板的设计决策

## ADR-001 前端

采用：

```text
Vben Admin 5 + Element Plus
```

AI Chat 主界面自研，不强行使用 CRUD 组件。

## ADR-002 后端

采用：

```text
FastAPI
```

## ADR-003 向量数据库

一期采用：

```text
Qdrant
```

## ADR-004 Collection

采用统一：

```text
knowledge_chunks
```

通过 Payload Filter 隔离知识库与组织。  
**前提：** 平台级统一 Embedding（见 ADR-009），禁止每 KB 不同 embedding_model / dimension。

## ADR-005 一期不使用 LangGraph

固定：

```text
Retrieve → Prompt → Generate
```

二期 / 三期再引入 Tool / Workflow / Agent。

## ADR-006 业务层不直接依赖 LangChain

LangChain 位于 AI Adapter / 编排实现内部。

## ADR-007 文档任务先抽象 Job

一期执行器可使用 BackgroundTasks / asyncio，未来切换 Celery / RQ 时保持 Job 状态模型不变。

## ADR-008 测试 Shift Left

测试与功能同步开发，不设置独立的「最后补测试阶段」。

```text
实现功能 → Unit → Integration/API → Lint/Typecheck → PR
```

Definition of Done 必须含测试；禁止「功能全部写完再集中补测试」。

## ADR-009 Chunk 真源与向量索引分离

```text
MySQL document_chunk = Chunk 全文真源
Qdrant               = 向量索引（payload 不含 content）
FileStorage          = 原始文档真源
```

检索：Qdrant 返回 `chunk_id[]` → MySQL 批量取全文 → Prompt。

## ADR-010 平台级 Embedding Config

Embedding 为平台（org）级配置，不进入 KB `rag_config`。

保证统一 collection + 多 KB `kb_id IN (...)` + Global Top-K 在同一向量空间内可行。

## ADR-011 Default Space

创建 Organization 时自动创建 Default Space。  
一期 Space 仅必要 CRUD + Member；不做嵌套 / 配额 / 权限继承 / Owner 转移。


# 20. Phase 0 退出标准

当前已完成设计草案：

- [x] 系统上下文
- [x] 模块边界
- [x] 依赖方向
- [x] 核心实体（含 `document_chunk` / `platform_ai_config`）
- [x] ER 草案（含关联表字段节）
- [x] Qdrant Payload（无全文）
- [x] API V1 草案 + Error Matrix 基线
- [x] SSE V1
- [x] 前端目录
- [x] 后端目录
- [x] Docker 服务边界
- [x] 环境变量基线
- [x] RBAC 基线
- [x] 关键 ADR（含 ADR-008～011）
- [x] R1–R6 审查项拍板（见 `v2-planning-review.md`）

Phase 0 还需要继续细化（落实，非方向未定）：

- [x] MySQL 字段级 DDL + 索引 + 唯一约束（含 `kb_id+file_hash`、`document_id+chunk_index`）→ [`docs/mysql/ddl_v1.sql`](./docs/mysql/ddl_v1.sql)
- [x] OpenAPI Request / Response Schema → [`docs/openapi-v1.yaml`](./docs/openapi-v1.yaml) + [`docs/api.md`](./docs/api.md)
- [x] Error Matrix 与路由鉴权对照表细化 → [`docs/api.md`](./docs/api.md)
- [x] SSE TypeScript 类型定义（草案）→ [`docs/sse-protocol.md`](./docs/sse-protocol.md)
- [x] SSE Python Pydantic 类型定义 → [`backend/app/schemas/sse.py`](./backend/app/schemas/sse.py)
- [x] docker-compose.yml 实际文件 → [`deploy/docker-compose.yml`](./deploy/docker-compose.yml)
- [x] 仓库脚手架 backend FastAPI + frontend Vben（web-ele）
- [ ] Alembic 初始 Migration（待 SQLAlchemy models 后 autogenerate）

---

# 21. 下一步

建议严格按照：

```text
数据库 ER + MySQL DDL V1
（含 document_chunk / platform_ai_config / Default Space / 唯一约束）
        ↓
API Schema + Error Matrix 细化
        ↓
SSE 类型定义
        ↓
Repository Skeleton
        ↓
docker-compose.yml
        ↓
Phase 1 编码（Shift-left 测试）
```

下一项直接开始：

> **Phase 1：Auth / RBAC + SQLAlchemy Models + Alembic**（脚手架已就绪）
