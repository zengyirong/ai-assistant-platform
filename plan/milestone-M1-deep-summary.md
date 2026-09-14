# 里程碑 M1 — 阶段深度总结

> 里程碑名称：**真实 RAG 主路径可演示**  
> 时间跨度：规划审查（R1–R6）→ Phase 0 / 0.5 → 后端主链路 → 业务 UI → 真实 LLM/Embedding 联调通过  
> 基准日期：2026-09-14  
> 关联：[问题与修复](./milestone-M1-bugs-and-fixes.md) · [下一里程碑 M2](./milestone-M2-next-goals.md)

---

## 1. 一句话结论

从「只有产品与设计文档」走到「本机可用的文档问答产品雏形」：  
**登录 → 知识库 → TXT/MD 入库向量化 → 真实检索 → 真实大模型流式回答 → Citation**，主路径已闭环，可演示、可继续迭代。

---

## 2. 历程回顾（审查 → 里程碑）

### 2.1 规划与审查（定方向）

| 产物 | 作用 |
|---|---|
| 产品规划 V2 | 一期 RAG 底座 → 二期医院 → 三期 HR；明确不做清单 |
| v2-planning-review（R1–R6） | DDL/Chunk 真源/Default Space/OpenAPI/健康检查与测试左移等全部拍板 |
| Phase 0 系统设计 | 架构、表、API、SSE、ADR、Compose 边界 |
| Phase 0.5 UI/UX + 审查 | IA、页面关系、状态与交互；**通过（带条件）** 后才开前端业务页 |

**补充认识：** 没有 Phase 0.5，前端极易边写边改；审查纪要里的 U1–U7（系统管理暂缓、本地筛选、Citation 侧栏优先等）被证明是正确的「减范围」策略。

### 2.2 工程契约与脚手架

- `docs/`：DDL、种子、API、OpenAPI、SSE 协议  
- `backend/` FastAPI + `frontend/` Vben Admin 5（web-ele）  
- Compose 默认 Qdrant；MySQL 本机；规划文档归拢到 `plan/`

### 2.3 后端主链路（先 fake，后真实）

按依赖顺序落地（符合 Shift-left 精神）：

```text
Auth/RBAC → KB/成员/RAG配置 → Document/Job(TXT·MD)
    → Embedding + Qdrant → Conversation + RAG SSE
```

默认 `LLM_PROVIDER=fake` / `EMBEDDING_PROVIDER=fake`，保证无外网也能测协议与权限；适配器预留 `openai_compatible`。

### 2.4 前端业务 UI（对齐 Phase 0.5）

- 菜单：智能问答 + 知识库（系统管理按 U1 暂缓）  
- 知识库列表/新建/详情（文档上传轮询、成员、RAG 编辑）  
- Chat 三栏：会话 | 对话 | Citation + SSE  

### 2.5 真实模型接通（里程碑封顶条件）

| 组件 | 选型（当前联调） |
|---|---|
| LLM | DeepSeek（OpenAI 兼容） |
| Embedding | 阿里云百炼 `text-embedding-v4`（1024 维） |
| 向量库 | 本机 Qdrant，collection `knowledge_chunks_aliyun` |

联调中解决了代理访问 Qdrant、Embedding 批次限制、流式观感等问题（详见 Bugs 文档），至此 **M1 达成**。

---

## 3. 里程碑定义与完成度

### 3.1 M1 目标（事后正式表述）

```text
在本地环境中，使用真实 Embedding + 真实 LLM，
完成「上传 TXT/MD → 就绪 → 问答有引用」的可重复演示路径。
```

### 3.2 对照产品规划 P0

| P0 项 | M1 状态 |
|---|---|
| 登录 / RBAC | 完成（管理端 UI API 未全开） |
| KB / Document | 完成（管理与上传主路径） |
| Parser | **部分**：TXT/MD 完成；PDF/DOCX 未完成 |
| Embedding / Vector | 完成（可切换厂商） |
| RAG / Citation / SSE / Conversation | 完成 |

结论：M1 = **P0 主路径演示版**，不是一期 DoD 全量完成。

### 3.3 明确「不算 M1 完成」的项

- PDF / DOCX 解析与页码级 Citation  
- 系统管理（用户/角色/空间/审计 UI+API）  
- Alembic 正式迁移流、CI、Golden Dataset、完整审计  
- 生产级密钥管理、限流、多租户隔离强化  
- Chat 正文角标 `[1][2]`（侧栏 Citation 已满足 Phase 0.5 优先策略）

---

## 4. 架构与决策沉淀

### 4.1 仍然正确的早期决策

1. **MySQL `document_chunk` 为全文真源，Qdrant 只存向量** — 换 Embedding/维度时语义清楚  
2. **平台级 Embedding**（非每 KB 自选模型）— 降低配置爆炸  
3. **统一 collection + kb 过滤** — 实现简单，够一期  
4. **SSE 协议先行** — 前后端并行、假/真 LLM 可切换  
5. **UI 审查带条件通过再编码** — 系统管理暂缓避免空菜单

### 4.2 联调后新增强约束（建议写入后续规范）

1. 本地向量库客户端 **禁用系统代理（trust_env=False）**  
2. Embedding 客户端必须可配置 **batch size**，默认兼容最严厂商（10）  
3. 变更向量维度 → **新 collection + 全量重索引**  
4. `.env` 变更 → **整进程重启**；示例配置进 `.env.example`，密钥永不入库  
5. 错误展示应区分「文件问题」与「依赖/配额问题」

### 4.3 概念澄清（易混点）

```text
向量数据库 = Qdrant 服务（QDRANT_URL）
QDRANT_COLLECTION = 库内集合名（索引分区），不是另一个数据库产品
Embedding 模型 = 生成向量的 API/本地模型（与选 Qdrant 还是 Chroma 无强绑定）
```

---

## 5. 交付物盘点

### 5.1 文档

- `plan/`：规划、Phase 0/0.5、审查纪要、本里程碑三件套  
- `docs/`：DDL / API / SSE  

### 5.2 后端能力

- Auth JWT；KB CRUD/成员/RAG；文档 Job；Qdrant；Chat SSE  
- Space 列表（创建 SPACE 可见知识库用）  
- fake / openai_compatible 双模式  

### 5.3 前端能力

- 真实后端代理；知识库全流程；Chat + Citation  
- 成员增删、RAG 编辑  

### 5.4 运行画像（本地）

```text
前端 pnpm run dev:ele  → 代理 /api → :8000/api/v1
后端 uvicorn :8000
MySQL 本机 · Qdrant Docker :6333
登录 admin / Admin@123456
```

---

## 6. 过程方法复盘（补充）

### 6.1 做得好的

- **先契约后编码、先 fake 后真实**，主链路很少推倒重来  
- **小闭环验收**：UI → 假模型 → 真模型，每段有可观测失败（job 原因、SSE error）  
- Bug 能落到「环境 / 供应商限制 / 产品范围」三类，而不是盲目改业务逻辑  

### 6.2 可改进的

- 完成记录 `项目已完成工作记录.md` 未及时同步「前端已完成 / 真实模型已通」— 建议以本总结为准更新  
- Job 错误码对用户不够友好；应用层可建错误码→文案表  
- 缺少一页「本地接通真实模型」Runbook（可从 Bugs §11 + 本文 §5.4 抽）  
- 自动化测试仍偏单元/部分 API；真实 Embedding/LLM 宜用可选集成测试 + mock  

### 6.3 风险与债（带入 M2）

| 风险/债 | 影响 | 建议归属 |
|---|---|---|
| PDF/DOCX 未解析 | 上传区文案与能力不一致 | M2 |
| 无用户搜索却要填 UUID 加成员 | 可用性差 | M2 或独立小迭代 |
| Key 与代理环境敏感 | 联调不稳定、安全 | 运维约定 + 文档 |
| Alembic 未成为唯一真相 | 环境漂移 | M2/M3 工程化 |
| Fake 与真模型行为差 | 测试结论不可直接外推 | 验收以真模型为准 |

---

## 7. 对「一期成功」的重新对齐

产品规划要求功能 + 权限 + 异常 + 审计 + 测试 + 文档。  
**M1 证明产品方向可行，并交付可演示主路径**；完整一期 DoD 仍需 M2（解析补齐）+ 后续工程化里程碑。

建议对外口径：

> 「文档智能问答 MVP 已可本地演示（TXT/MD + 真实模型）；办公文档格式与工程化仍在下一阶段。」

---

## 8. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 初版：审查至 M1 深度总结 |
