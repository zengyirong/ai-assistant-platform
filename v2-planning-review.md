# AI 智能助手产品规划 V2 — 审查报告

> 审查对象：[AI智能助手产品规划_V2.md](./AI智能助手产品规划_V2.md)  
> Phase 0 对照：[AI智能助手平台_Phase0_系统设计_V1.md](./AI智能助手平台_Phase0_系统设计_V1.md)  
> 版本：V2.0 / 2026-09-11；决议更新：2026-09-12  
> 审查日期：2026-09-11  
> 仓库状态：greenfield（规划 + Phase 0 设计；R1–R6 已在 Phase 0 拍板）

---

## 1. 总评

**可以按文档逐步执行。** 无推翻架构的致命矛盾。

产品边界、演进原则、一期 MVP、领域隔离、SSE V1、权限必须在检索前过滤、Document Job 状态机、Definition of Done / 质量门禁均清晰，适合作为 greenfield 的源真理。

**R1–R6 已于 2026-09-12 在 Phase 0 拍板，不再保持 open。** 后续工作是把决议落实为 DDL / OpenAPI / ADR 正文与代码，而不是继续争论方向。

下一跳：

```text
MySQL DDL V1（含 document_chunk + 关联表 + 索引）
    ↓
OpenAPI Schema + Error Matrix
    ↓
SSE 类型 / docker-compose / 脚手架
    ↓
一期开发（Shift-left 测试）
```

---

## 2. 缺陷与决议（已拍板）

严重度说明（历史分类；决议后统一进入「落实」阶段）：

| 级别 | 含义 |
|---|---|
| P0 | 曾阻塞可靠实现；现已拍板 |
| P1 | 一致性 / 节奏；现已拍板 |

---

### R1. ER 不完整 → **resolved（补齐）**

**Phase 0 决策**

- 补齐关联表字段：`space_member`、`sys_user_role`、`sys_role_permission`
- 补齐唯一约束、索引、字段级 DDL
- 新增 `document_chunk`、`platform_ai_config`（见 R2 / R5）

**落实跟踪**

- [x] Phase 0 §6 关联表字段节
- [x] MySQL DDL V1 + 种子脚本（[`docs/mysql/ddl_v1.sql`](./docs/mysql/ddl_v1.sql)、[`docs/database.md`](./docs/database.md)）
- [ ] Alembic 初始 migration（脚手架时与 SQLAlchemy models 对齐）

---

### R2. Chunk 落库 → **resolved（MySQL 为全文真源）**

**Phase 0 决策**

新增表 `document_chunk`：

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

Qdrant payload **不含全文**，仅索引过滤字段：

```json
{
  "org_id": "org_1",
  "kb_id": "kb_1",
  "document_id": "doc_1",
  "chunk_id": "chunk_123",
  "page": 12,
  "section": "年假制度"
}
```

检索链路：

```text
Question → Embedding → Qdrant Search → chunk_id[]
  → MySQL 批量查 document_chunk → Prompt Context
```

职责分离：

```text
MySQL       = Chunk 内容真源
Qdrant      = 向量搜索索引
FileStorage = 原始文档真源
```

**落实跟踪**

- [x] 决议写入本文件与 Phase 0
- [x] DDL / Qdrant payload / RAG 流程章节对齐（[`docs/mysql/ddl_v1.sql`](./docs/mysql/ddl_v1.sql) 含 `document_chunk`）

---

### R3. space / org_id → **resolved（收敛）**

**Phase 0 决策**

```text
Organization
    └── Default Space（创建组织时自动创建）
```

一期用户可用：

- Private KB
- Space KB（挂在默认空间或显式选择的 Space）

Space API **只保留必要**：列表 / 详情 / 创建 / 修改 / 成员管理。

一期不做：

- 复杂部门树
- Space 嵌套
- Space 权限继承
- Space 配额
- Space Owner 转移流程
- 完整 Organization 管理 API（org 由种子 / 配置绑定即可）

**落实跟踪**

- [x] 决议写入
- [ ] Phase 0 Space 范围说明 + 默认空间种子规则

---

### R4. API 清单 → **resolved（补齐）**

**Phase 0 决策**

- FastAPI Pydantic Schema → 生成 OpenAPI
- **另行手工维护** Request / Response / **Error Matrix**
- 原则：**OpenAPI ≠ API 设计**；错误码矩阵为契约一等公民
- 停止生成：仅 AbortController + 后端感知断开（无独立 abort HTTP API）

错误码矩阵基线：

| HTTP | Code | 场景 |
| ---: | --- | --- |
| 400 | `VALIDATION_ERROR` | 参数错误 |
| 401 | `AUTH_UNAUTHORIZED` | 未登录 / Token 无效 |
| 403 | `PERMISSION_DENIED` | 功能权限不足 |
| 403 | `KB_PERMISSION_DENIED` | 无 KB 数据权限 |
| 404 | `KB_NOT_FOUND` | KB 不存在 |
| 404 | `DOCUMENT_NOT_FOUND` | 文档不存在 |
| 409 | `DOCUMENT_DUPLICATED` | KB 内重复文件 |
| 422 | `DOCUMENT_PARSE_FAILED` | 文档不可解析 |
| 429 | `LLM_RATE_LIMIT` | 模型限流 |
| 503 | `VECTOR_STORE_UNAVAILABLE` | Qdrant 不可用 |
| 504 | `LLM_TIMEOUT` | LLM 超时 |
| 500 | `INTERNAL_ERROR` | 未预期异常 |

**落实跟踪**

- [x] 错误码基线写入
- [ ] Phase 0 Error Matrix 专节 + OpenAPI Schema 细化

---

### R5. 一致性 → **resolved（全部拍板）**

含一项重要架构调整：**平台级 Embedding，禁止每 KB 不同 embedding_model**。

| 项 | 决议 |
|---|---|
| Health | `GET /health`、`GET /ready`（**不**挂 `/api/v1`；属基础设施） |
| File Hash | `SHA-256(raw file bytes)` |
| 去重范围 | 唯一约束 `kb_id + file_hash`：同 KB 重复 → `DOCUMENT_DUPLICATED`；跨 KB 允许 |
| 多 KB 检索 | **一次** Qdrant Search + `kb_id IN (...)` + **Global Top-K**（不是每 KB 各查再 merge） |
| Embedding | **平台级** `PlatformAIConfig`（model / dimension / provider）；`rag_config` **删除** `embedding_model` |
| 代码门禁 | Frontend: ESLint + Prettier + Stylelint + vue-tsc；Backend: Ruff + Black + mypy + Pytest |

`rag_config`（KB 级）仅保留：

```text
chunk_strategy
chunk_size
chunk_overlap
top_k
score_threshold
llm_model
temperature
system_prompt
```

`PlatformAIConfig`：

```text
embedding_model
embedding_dimension
embedding_provider
```

原因：统一 `knowledge_chunks` collection + 多 KB 一次检索，要求同一 Embedding 空间与维度；每 KB 自选 embedding_model 会与统一 collection 冲突。

**落实跟踪**

- [x] 决议写入
- [ ] Phase 0：去掉 KB `embedding_model`、补平台配置、RAG/Qdrant/Hash 专节

---

### R6. 测试节奏 → **resolved（ADR-008）**

**Phase 0 决策 / ADR-008**

> **测试采用 Shift Left：测试与功能同步开发，不设置独立的「最后补测试阶段」。**

```text
实现功能 → Unit Test → Integration / API Test → Lint + Type Check → PR
```

DoD：

```text
代码 ≠ 完成
代码 + 测试 + 权限 + 异常 + 日志 + 文档 = Done
```

**落实跟踪**

- [x] 决议写入
- [ ] Phase 0 写入 ADR-008 正文

---

## 3. 范围外（不影响一期开工）

- 二期医院 AI 工作台细节
- 三期 HR / Agent / Human-in-the-loop 细节
- 面试叙事（产品规划 §42）
- 质量门禁长文 —— 脚手架按 R5 精简子集落地

---

## 4. Phase 0 默认参数（定稿）

| 项 | 默认值 |
|---|---|
| `chunk_size` | 800 |
| `chunk_overlap` | 120 |
| `top_k` | 5（Global Top-K） |
| `score_threshold` | 可配置，Golden Dataset 校准 |
| 上传大小上限 | 20MB |
| 支持格式 | PDF / DOCX / TXT |
| 向量库 | 一期 Qdrant（统一 collection `knowledge_chunks`） |
| Embedding | 平台级单一模型 / 维度 |
| 队列 | BackgroundTasks + Job 抽象 |
| File Hash | SHA-256；去重 `kb_id + file_hash` |

---

## 5. 闭环跟踪

| ID | 项 | 严重度 | 状态 | 落实物 |
|---|---|---|---|---|
| R1 | ER + DDL + Index | P0 | **resolved** → DDL 已落盘 | [`docs/database.md`](./docs/database.md), [`docs/mysql/ddl_v1.sql`](./docs/mysql/ddl_v1.sql) |
| R2 | document_chunk / MySQL 真源 | P0 | **resolved** → DDL 已落盘 | `document_chunk` 表已建 |
| R3 | Default Space | P0 | **resolved** | Phase 0 + `seed_v1.sql` |
| R4 | OpenAPI + Error Matrix | P0 | **resolved** → 已落盘 | [`docs/api.md`](./docs/api.md), [`docs/openapi-v1.yaml`](./docs/openapi-v1.yaml) |
| R5 | Embedding / Hash / Multi-KB / Health / Lint | P1 | **resolved** | Phase 0 + `platform_ai_config` DDL + Compose |
| R6 | Shift-left Testing | P1 | **resolved** | ADR-008 |

状态约定：`resolved` = 方向已拍板并写入设计；`implemented` = 代码已落地。

---

## 5.1 Phase 0 对照（2026-09-12 决议后）

对照文档：[AI智能助手平台_Phase0_系统设计_V1.md](./AI智能助手平台_Phase0_系统设计_V1.md)

**总评：** R1–R6 方向已全部拍板。Phase 0 文档须同步改写旧草案（尤其原「chunk content 进 Qdrant」「KB 级 embedding_model」）。文档自身 §20 的 DDL / OpenAPI / compose 实文件仍属**落实项**，不是方向未定。

---

## 6. Phase 0 当前落实清单

```text
R1  ER + DDL + Index     ✅ docs/mysql/ddl_v1.sql
R2  document_chunk       ✅
R3  Default Space        ✅ seed_v1.sql
R4  OpenAPI + Error Matrix  ✅ docs/api.md / openapi-v1.yaml
R5  PlatformAIConfig / Hash / Global Top-K / Health / 门禁  ✅
R6  ADR-008 Shift-left   ✅
```

---

## 7. 结论

V2 规划 + Phase 0 拍板决议可作为一期实施依据。

**DDL / API / SSE / Compose / 脚手架已落地。** 下一优先项：**Phase 1 Auth + SQLAlchemy Models**。
