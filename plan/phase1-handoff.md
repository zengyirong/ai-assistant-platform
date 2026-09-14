# 一期交接 / 演示说明

> 对应里程碑：[M6](./milestone-M6-next-goals.md)  
> 更新日期：2026-09-14  
> 范围：文档 RAG 智能查询助手（平台底座）一期可交接态

---

## 1. 演示账号与端口

| 项 | 值 |
|---|---|
| 演示登录 | `admin` / `Admin@123456`（ADMIN）；`demo` / `Demo@123456`（USER） |
| 后端 | `http://127.0.0.1:8000`（`uvicorn … --port 8000`） |
| 前端 | 通常 `http://localhost:5777`（`pnpm run dev:ele`） |
| 健康检查 | `GET /health`、`GET /ready`（MySQL + Qdrant） |

---

## 2. 本地启动（最短路径）

```bash
# 1) 依赖服务（本机 MySQL 可不进 Docker；至少起 Qdrant）
docker compose -f deploy/docker-compose.yml up -d

# 2) 环境变量
cp .env.example .env
# 编辑 MYSQL_*；演示可用 fake LLM/Embedding

# 3) 库表 + 种子（新库）
cd backend
alembic upgrade head
# 再导入 docs/mysql/seed_v1.sql（见 backend/README.md）

# 4) API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5) 前端（另开终端）
cd frontend
pnpm install
pnpm run dev:ele
```

细节（迁移 stamp、`.env`、测试）：[backend/README.md](../backend/README.md)

---

## 3. 演示路径（主路径）

```text
登录 admin
  → 知识库：新建 / 打开
  → 文档：上传 txt|md|pdf|docx → 等 Job 成功
  → 问答：选 KB → 提问 → 看流式回答与引用
  →（可选）成员：从本 org 用户列表加人
  →（ADMIN）审计日志：侧栏「审计日志」或 GET /api/v1/audit-logs
```

**可选 API（M6）**：`POST /api/v1/users`（仅 ADMIN）同 org 创建 `USER`，便于成员协作演示，无需手写 SQL。

---

## 4. 回归命令

```bash
cd backend
ruff check .
pytest                 # 需 MySQL + seed + Qdrant
pytest tests/unit tests/rag_eval -q   # 离线子集
```

CI：`.github/workflows/backend-ci.yml`

---

## 5. 已知限制（一期）

- 默认 `LLM_PROVIDER` / `EMBEDDING_PROVIDER=fake` 可离线演示；真实模型需改 `.env` 并注意维度与 collection
- 无 Redis / Celery / MinIO / OCR / Rerank / Hybrid Search（规划 P2）
- **完整系统管理**（组织/角色/菜单全套）未做；能力债见产品 IA，另立里程碑
- 审计写入 best-effort，失败不阻断业务

---

## 6. Bugs 索引

| 文档 | 内容 |
|---|---|
| [milestone-M1-bugs-and-fixes.md](./milestone-M1-bugs-and-fixes.md) | B1–B12 |
| [milestone-M4-M5-bugs-and-fixes.md](./milestone-M4-M5-bugs-and-fixes.md) | B13–B14（登录死循环 / 错误文案） |

---

## 7. 里程碑完成说明

| ID | 文档 |
|---|---|
| M1–M5 | `plan/milestone-M*-completion.md` |
| M6 | [milestone-M6-completion.md](./milestone-M6-completion.md)（已验收） |
