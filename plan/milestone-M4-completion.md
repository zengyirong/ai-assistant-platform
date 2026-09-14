# 里程碑 M4 — 完成说明（验收通过）

> 状态：**已完成**（2026-09-14 验收通过）  
> 目标文档：[milestone-M4-next-goals.md](./milestone-M4-next-goals.md)  
> 前置：[M3 完成说明](./milestone-M3-completion.md)

---

## 1. 一句话结论

**协作与可理解性补齐**：组织内用户可搜索加入知识库；常见 API `code` 有稳定中文提示；文档列表可感知 Job 进度与失败原因。审计日志未纳入本里程碑 Must（留给 M5）。

---

## 2. DoD 对照

| 退出标准 | 结果 |
|---|---|
| 管理员可为 KB 通过用户搜索添加/移除成员 | 通过（含行内改角色） |
| 上传失败与解析失败有可读错误 | 通过（`error-messages.ts` + Job 弹窗） |
| 文档处理状态在 UI 可感知 | 通过（`latest_job` 进度 % / 阶段） |
| 回归不破坏 M1–M3 主路径 | 通过（后端 pytest 含 users 冒烟） |
| plan 完成说明 | 本文 |

---

## 3. 技术落地摘要

| 项 | 说明 |
|---|---|
| 用户搜索 | `GET /api/v1/users?q=`（本 org ACTIVE；`modules/user`） |
| 成员 DTO | `username` / `nickname`；添加时校验同组织用户 |
| 前端成员 | `detail.vue` remote `ElSelect`；行内改角色（复用 upsert） |
| 错误文案 | `frontend/.../utils/error-messages.ts`；拦截器 / Job / Chat SSE |
| Job 进度 | `document_to_dict.latest_job`；列表展示阶段 + `%` |
| 契约 | `docs/api.md` 补 Users 路由 |

### 明确不做（仍有效）

- 完整系统管理后台  
- Redis / Celery / MinIO  
- OCR、Rerank、Hybrid Search、完整 CD  

---

## 4. Should 未做（带入 M5）

| 项 | 说明 |
|---|---|
| 审计日志写入 | 上传 / 删文档 / 改成员等写操作落 `audit_log`；只读查询可后置 |
| Citation 边角 | 正文角标与侧栏一致性说明等小修 |

---

## 5. 已知限制

1. Seed 默认仅 `admin` 时，成员搜索演示需再建同组织用户，或临时自测搜 `admin`  
2. 错误文案：**有后端 `message` 优先展示**；无 message 时用 code 映射（见 [B14](./milestone-M4-M5-bugs-and-fixes.md#3-b14--登录错误提示与后端-message-不一致)）  
3. Job 进度依赖列表轮询 + `latest_job`，非 WebSocket  

---

## 5.1 验收后补丁（仍属 M4 错误体系收尾）

| ID | 内容 | 状态 |
|---|---|---|
| [B14](./milestone-M4-M5-bugs-and-fixes.md) | code 映射盖住登录失败文案 | 已修复（`84323ed`） |

框架侧登录 401→logout 死循环见同文档 **B13**（非 M4 引入，M5 联调暴露）。

---

## 6. 建议 commit

```text
feat: M4 成员搜索、错误文案与文档 Job 进度

组织用户搜索 API；KB 成员选择器；前端 code→中文；文档列表 latest_job。
```

固化文档：

```text
docs: 固化 M4 验收完成说明并规划 M5
```

Bugs 归档：

```text
docs: 归档 M4/M5 联调 Bugs B13/B14
```

---

## 7. 下一步

→ **[里程碑 M5 — 可追溯与运维增强](./milestone-M5-next-goals.md)**（进行中）  
→ Bugs：[milestone-M4-M5-bugs-and-fixes.md](./milestone-M4-M5-bugs-and-fixes.md)

---

## 8. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 验收通过；完成本说明 |
| 2026-09-14 | 补丁说明：B14 错误文案优先级；交叉引用 B13/B14 归档 |