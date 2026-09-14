# 里程碑 M3 — 目标规划（工程化）

> 前置： [M2 完成说明](./milestone-M2-completion.md) 已验收  
> 依据：产品规划 V2 §P1、Phase 0 ADR-008、M1/M2 遗留工程债  
> 日期：2026-09-14  
> 状态：**已完成** → [milestone-M3-completion.md](./milestone-M3-completion.md)

---

## 1. 一句话目标

**把「能演示」变成「可重复交付」：数据库迁移、自动化测试与 CI 成为默认工作流。**

---

## 2. Must（必须）

1. **Alembic**
   - [x] 初始 revision `20260914_0001`（对齐 `docs/mysql/ddl_v1.sql`）
   - [x] 文档约定：新环境以 `alembic upgrade head` 为准；手工 DDL 仅作参考  
2. **核心自动化测试**
   - [x] conftest 强制 `LLM_PROVIDER` / `EMBEDDING_PROVIDER=fake`
   - [x] Parser / unit + Auth/KB API 冒烟（CI 内带 MySQL）  
3. **CI 最小流水线**
   - [x] `.github/workflows/backend-ci.yml`：ruff + alembic + seed + pytest  

---

## 3. Should

- [x] Golden Dataset 起步（`tests/rag_eval/`）  
- [x] `message_citation` FK → `ON DELETE CASCADE`（revision `20260914_0002`）  
- [x] `/ready` 与本地 Runbook 写入 `backend/README`  

---

## 4. Won’t

- 系统管理全套 UI  
- Redis / Celery / MinIO  
- OCR、Rerank、Hybrid Search  

---

## 5. 退出标准

```text
☑ 新库仅靠 Alembic 可建到与现网一致的主表结构
☑ CI 对 main/PR 跑通基础测试（workflow 已就位）
☑ README 写清：启动、迁移、测试、.env 注意点
☑ M2 能力（PDF/DOCX）不被回归破坏（parsers 单测 + golden smoke）
☑ 本地：ruff + pytest 22 passed（2026-09-14 验收）
```

---

## 6. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 初版：M2 验收后的下一里程碑 |
| 2026-09-14 | 落地 Alembic / CI / fake 测试 / README / citation CASCADE |
| 2026-09-14 | **验收通过** → [milestone-M3-completion.md](./milestone-M3-completion.md)；下一里程碑见 M4 |
