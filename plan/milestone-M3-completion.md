# 里程碑 M3 — 完成说明（验收通过）

> 状态：**已完成**（2026-09-14 验收通过）  
> 目标文档：[milestone-M3-next-goals.md](./milestone-M3-next-goals.md)  
> 前置：[M2 完成说明](./milestone-M2-completion.md)

---

## 1. 一句话结论

**「能演示」已变成「可重复交付」**：新环境以 Alembic 建库，本地与 CI 默认可在 fake Provider 下跑通回归；`backend/README` 写清启动 / 迁移 / 测试 / `.env` 注意点。

---

## 2. DoD 对照

| 退出标准 | 结果 |
|---|---|
| 新库仅靠 Alembic 可建到与现网一致的主表结构 | 通过（`20260914_0001` + `0002`） |
| CI 对 main/PR 跑通基础测试 | 通过（workflow 已就位；路径触发） |
| README 写清：启动、迁移、测试、.env | 通过（`backend/README.md`） |
| M2 能力（PDF/DOCX）不被回归破坏 | 通过（parsers 单测 + golden smoke） |
| 本地验收：`ruff check .` + `pytest -q` | 通过（**22 passed**，2026-09-14） |

---

## 3. 技术落地摘要

| 项 | 说明 |
|---|---|
| 初始迁移 | `backend/alembic/versions/20260914_0001_initial_schema.py`（对齐 DDL） |
| CASCADE | `20260914_0002_citation_cascade.py`：`message_citation` → document/chunk `ON DELETE CASCADE` |
| 已有库接入 | `alembic stamp 20260914_0001` → `alembic upgrade head` |
| 测试默认 | `tests/conftest.py` 强制 `LLM_PROVIDER` / `EMBEDDING_PROVIDER=fake` |
| Golden 起步 | `tests/rag_eval/golden_samples.json` + `test_golden_smoke.py` |
| CI | `.github/workflows/backend-ci.yml`：MySQL + Qdrant + ruff + migrate + seed + pytest |
| Runbook | `backend/README.md`（含 `/ready`、迁移、`.env`） |
| 环境修复 | `alembic.ini` ASCII；URL `%` 转义；去掉 `app.db`↔models 循环导入 |

### 明确不做（仍有效）

- 系统管理全套 UI  
- Redis / Celery / MinIO  
- OCR、Rerank、Hybrid Search  
- 完整 CD（自动部署）— 本里程碑仅为 CI  

---

## 4. 对 M2 遗留项的关闭

| 项 | 结果 |
|---|---|
| Alembic / CI / Golden Dataset | **已完成** |
| `message_citation` 无 CASCADE、靠应用层先删 | **库级 CASCADE 已落地**（应用层清理仍保留作双保险） |

---

## 5. 已知限制（带入后续）

1. GitHub Actions 需推远程后才实际跑绿；本地验收已覆盖同等检查项  
2. Golden Dataset 仅为 parse/chunk 离线烟雾，尚无检索质量评分  
3. Docker MySQL init 仍可挂 DDL 作 fallback；新环境优先 Alembic  
4. 体验与治理（成员、审计、错误文案、上传进度）→ **M4**

---

## 6. 建议 commit（若尚未提交工程化改动）

```text
feat: M3 工程化 — Alembic、CI 与 fake 测试默认路径

新环境以 alembic upgrade head 建库；CI 跑 ruff/pytest；citation FK CASCADE。
```

本文档可随「固化文档」单独或一并提交：

```text
docs: 固化 M3 验收完成说明并规划 M4
```

---

## 7. 下一步

→ **[里程碑 M4 — 体验与治理](./milestone-M4-next-goals.md)**：用户列表/加成员体验、审计日志、错误文案体系、上传进度。

---

## 8. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 验收通过（ruff + pytest 22 passed）；完成本说明 |
