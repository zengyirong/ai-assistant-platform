# 里程碑 M5 — 完成说明（验收通过）

> 状态：**已完成**（2026-09-14 验收通过并固化）  
> 目标文档：[milestone-M5-next-goals.md](./milestone-M5-next-goals.md)  
> 前置：[M4 完成说明](./milestone-M4-completion.md)  
> 联调 Bugs：[milestone-M4-M5-bugs-and-fixes.md](./milestone-M4-M5-bugs-and-fixes.md)（B13 / B14）

---

## 1. 一句话结论

**关键写操作可追溯**：登录/登出、文档上传删除重试、KB 成员变更写入 `audit_log`（best-effort）；ADMIN 可通过 API 与侧栏「审计日志」按时间查询。一期规划 P1 中的 **Audit** 项关闭。

---

## 2. DoD 对照

| 退出标准 | 结果 |
|---|---|
| 上传/删文档/改成员后 audit_log 有对应记录 | 通过 |
| ADMIN 可按时间查询审计列表（API + UI） | 通过（`/audit/list`） |
| 主路径回归不破坏 | 通过（含 `tests/api/test_audit.py`；联调修 B13/B14） |
| plan 完成说明 | 本文 |

---

## 3. 技术落地摘要

| 项 | 说明 |
|---|---|
| 模型 | `app/models/audit.py` → 表 `audit_log`（已在初始 Alembic 中） |
| 写入 | `modules/audit/service.write_audit`：独立 session；失败只打日志 |
| 动作 | `auth.login` / `auth.logout` / `document.upload\|delete\|retry` / `kb.member.upsert\|remove` |
| 查询 | `GET /api/v1/audit-logs`（仅 ADMIN；`action` / `user_id` 可选） |
| UI | `views/audit/list.vue` + `router/.../audit.ts`（`authority: ['ADMIN']`） |
| 契约 | `docs/api.md` §4.1.2 |

### 明确不做（仍有效）

- Redis / Celery / MinIO  
- OCR、Rerank、Hybrid Search、完整 CD  
- 完整系统管理后台  

---

## 4. Should 未做（已结转 M6）

| 项 | 说明 |
|---|---|
| Citation / 会话边角 | 仍结转后续（M6 未选） |
| Golden Dataset 增强 | **M6 已做** |
| 同 org 建 USER 薄 API | **M6 已做** |

---

## 5. 联调补丁（验收同期）

| ID | 内容 | 引入方 | 状态 |
|---|---|---|---|
| B13 | 错密触发 logout 401 死循环 | 原框架 | 已修 |
| B14 | Toast 盖住后端「用户名或密码错误」 | M4 错误 map | 已修 |

详见 [Bugs 归档](./milestone-M4-M5-bugs-and-fixes.md)。提交参考：`84323ed`。

---

## 6. 建议 commit（文档）

```text
docs: 固化 M5 验收完成说明并规划一期收口 M6
```

---

## 7. 下一步

→ 一期已收口，见 **[M6 完成说明](./milestone-M6-completion.md)** 与 **[交接说明](./phase1-handoff.md)**。

一期产品规划 **P0 + P1（Audit/工程化/体验）** 主线已齐；**P2**（Redis/Celery/MinIO/OCR…）仍后置。

---

## 8. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 验收通过并固化；完成本说明 |
