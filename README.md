# AI Assistant Platform

一期文档 RAG 智能查询助手（平台底座）。

## 文档

| 文档 | 说明 |
|---|---|
| [项目已完成工作记录.md](./项目已完成工作记录.md) | 已完成项汇总（本里程碑） |
| [AI智能助手产品规划_V2.md](./AI智能助手产品规划_V2.md) | 产品范围与分期 |
| [AI智能助手平台_Phase0_系统设计_V1.md](./AI智能助手平台_Phase0_系统设计_V1.md) | Phase 0 系统设计 |
| [v2-planning-review.md](./v2-planning-review.md) | 审查决议闭环 |
| [docs/database.md](./docs/database.md) | 数据库设计 V1 |
| [docs/mysql/ddl_v1.sql](./docs/mysql/ddl_v1.sql) | MySQL DDL |
| [docs/mysql/seed_v1.sql](./docs/mysql/seed_v1.sql) | 开发种子数据 |
| [docs/api.md](./docs/api.md) | API + Error / 鉴权矩阵 |
| [docs/openapi-v1.yaml](./docs/openapi-v1.yaml) | OpenAPI 3.1 |
| [docs/sse-protocol.md](./docs/sse-protocol.md) | SSE 协议 V1 |
| [deploy/docker-compose.yml](./deploy/docker-compose.yml) | MySQL + Qdrant |

## 当前进度

- [x] 产品规划 V2
- [x] Phase 0 设计 + R1–R6 拍板
- [x] MySQL DDL V1
- [x] OpenAPI / Error Matrix / SSE
- [x] docker-compose（MySQL + Qdrant）
- [ ] 仓库脚手架（FastAPI + Vben）
- [ ] Phase 1 编码

## 本地依赖

```bash
docker compose -f deploy/docker-compose.yml up -d
cp .env.example .env
```

首次启动 MySQL 会自动执行 `docs/mysql/ddl_v1.sql` 与 `seed_v1.sql`。

