# AI Assistant Platform

一期文档 RAG 智能查询助手（平台底座）。

## 文档

| 文档 | 说明 |
|---|---|
| [项目已完成工作记录.md](./项目已完成工作记录.md) | 已完成项汇总 |
| [plan/AI智能助手产品规划_V2.md](./plan/AI智能助手产品规划_V2.md) | 产品范围与分期 |
| [plan/v2-planning-review.md](./plan/v2-planning-review.md) | 审查决议闭环 |
| [plan/AI智能助手平台_Phase0_系统设计_V1.md](./plan/AI智能助手平台_Phase0_系统设计_V1.md) | Phase 0 系统设计 |
| [plan/AI智能助手平台_Phase0.5_UIUX设计_V1.md](./plan/AI智能助手平台_Phase0.5_UIUX设计_V1.md) | Phase 0.5 UI/UX |
| [plan/phase0.5-uiux-review.md](./plan/phase0.5-uiux-review.md) | Phase 0.5 审查纪要 |
| [plan/README.md](./plan/README.md) | 规划文档索引 |
| [plan/phase1-handoff.md](./plan/phase1-handoff.md) | **一期交接 / 演示说明** |
| [docs/database.md](./docs/database.md) | 数据库设计 V1 |
| [docs/api.md](./docs/api.md) | API + Error / 鉴权矩阵 |
| [docs/openapi-v1.yaml](./docs/openapi-v1.yaml) | OpenAPI 3.1 |
| [docs/sse-protocol.md](./docs/sse-protocol.md) | SSE 协议 V1 |
| [deploy/docker-compose.yml](./deploy/docker-compose.yml) | MySQL + Qdrant |
| [backend/README.md](./backend/README.md) | FastAPI 后端 |
| [frontend/PROJECT.md](./frontend/PROJECT.md) | Vben Admin 5（web-ele） |

## 当前进度

- [x] 产品规划 V2 / Phase 0 / DDL / API / SSE / Compose
- [x] 仓库脚手架（FastAPI + Vben web-ele 精简）
- [x] Phase 1：Auth + KB / Document / RAG / Citation / SSE（M1）
- [x] Phase 1：PDF/DOCX（M2）+ Alembic/CI（M3）+ 体验（M4）+ 审计（M5）
- [x] 前端对接真实后端（知识库 / 文档 / Chat / 审计）
- [x] **M6 一期收口**（交接说明 + USER/Golden；见 `plan/milestone-M6-completion.md` / `plan/phase1-handoff.md`）

## 本地启动

```bash
# 向量库（本机 MySQL 不走 Docker）
docker compose -f deploy/docker-compose.yml up -d

# 配置本机 MySQL 密码
cp .env.example .env
# 编辑 .env：MYSQL_USER / MYSQL_PASSWORD

# 初始化库表（PowerShell）
.\scripts\init_local_mysql.ps1 -Password "你的MySQL密码"

# 后端
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
uvicorn app.main:app --reload --port 8000

# 前端（另开终端）
cd frontend
pnpm install
pnpm run dev:ele
```

验证：`http://127.0.0.1:8000/ready` 应显示 `mysql` / `qdrant` 均为 ok。
