# 里程碑 M3 — 下一目标规划（工程化）

> 前置： [M2 完成说明](./milestone-M2-completion.md) 已验收  
> 依据：产品规划 V2 §P1、Phase 0 ADR-008、M1/M2 遗留工程债  
> 日期：2026-09-14

---

## 1. 一句话目标

**把「能演示」变成「可重复交付」：数据库迁移、自动化测试与 CI 成为默认工作流。**

---

## 2. Must（必须）

1. **Alembic**
   - 基于当前 Models 生成初始 revision（或对齐 `docs/mysql/ddl_v1.sql`）
   - 文档约定：新环境以 `alembic upgrade head` 为准；手工 DDL 仅作参考  
2. **核心自动化测试**
   - 现有 unit/api 测试可在无真实 LLM Key 下跑通（fake 默认）  
   - Parser / Auth / KB 冒烟稳定  
3. **CI 最小流水线**
   - 例如：lint（ruff）+ pytest（backend）  
   - 不强制调用付费 Embedding/LLM  

---

## 3. Should

- Golden Dataset 起步（少量问答样例 + 离线/fake 断言）  
- `message_citation` FK 改为 `ON DELETE CASCADE`（迁移修订，替代纯应用层清理）  
- `/ready` 与本地 Runbook 写进 `backend/README`  

---

## 4. Won’t

- 系统管理全套 UI  
- Redis / Celery / MinIO  
- OCR、Rerank、Hybrid Search  

---

## 5. 退出标准

```text
□ 新库仅靠 Alembic 可建到与现网一致的主表结构
□ CI 对 main/PR 跑通基础测试
□ README 写清：启动、迁移、测试、.env 注意点
□ M2 能力（PDF/DOCX）不被回归破坏
```

---

## 6. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 初版：M2 验收后的下一里程碑 |
