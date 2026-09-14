# 里程碑 M6 — 完成说明（验收通过）

> 状态：**已完成**（2026-09-14 验收通过并固化）  
> 目标文档：[milestone-M6-next-goals.md](./milestone-M6-next-goals.md)  
> 前置：[M5 完成说明](./milestone-M5-completion.md)  
> 交接入口：[phase1-handoff.md](./phase1-handoff.md)

---

## 1. 一句话结论

**一期底座可交接**：演示与运维路径写清；同 org 建 USER + seed 演示账号补齐成员协作；Golden 离线断言增强。不进入 P2 / 完整系统管理。

---

## 2. DoD 对照

| 退出标准 | 结果 |
|---|---|
| 交接/演示说明落盘 | 通过（`plan/phase1-handoff.md`） |
| 主路径回归通过 | 通过（`ruff` + `pytest` **26 passed**） |
| （可选）选定 Should | 通过：USER 薄 API + Golden；Citation 未选 |
| plan 完成说明 | 本文 |

---

## 3. 技术落地摘要

| 项 | 说明 |
|---|---|
| 交接 | `plan/phase1-handoff.md`：启动、演示路径、限制、Bugs 索引 |
| 建 USER | `POST /api/v1/users`（ADMIN）；绑定 `USER` 角色；审计 `user.create`；冲突 `USER_NAME_CONFLICT` |
| Seed 演示账号 | `demo` / `Demo@123456`（USER）；默认空间 MEMBER |
| Golden | `golden_samples.json` 多样本；`min_chunks` + 问句 keyword 排序断言 |
| 契约 | `docs/api.md` §4.1.1 / Error Matrix；前端 `USER_NAME_CONFLICT` 文案 |
| 提交参考 | `50acf26`（能力）；seed `demo` 随本固化一并落盘 |

### 明确不做（仍有效）

- 完整系统管理后台（组织/角色/菜单全套）— 另立里程碑  
- Redis / Celery / MinIO / OCR / Rerank / Hybrid Search（P2）  
- 完整 CD  

---

## 4. Should 未做（结转后续）

| 项 | 说明 |
|---|---|
| Citation / 会话边角 | 角标与侧栏一致性等小修 |

---

## 5. 演示账号（seed）

| 用户 | 密码 | 角色 |
|---|---|---|
| `admin` | `Admin@123456` | ADMIN |
| `demo` | `Demo@123456` | USER |

---

## 6. 建议 commit（文档 + seed）

```text
docs: 固化 M6 一期收口完成说明；seed 增加 demo 演示账号
```

---

## 7. 下一步

一期 **P0 + P1 主线已收口**。可选方向（另立里程碑，勿默认膨胀）：

1. **系统管理**（用户/角色/**菜单**/空间 UI）— 完整 RBAC 闭环；见 [M7](./milestone-M7-next-goals.md)  
2. Citation / 会话体验小修  
3. **P2**：Redis / Celery / MinIO / OCR / Rerank / Hybrid Search  

日常演示与交接以 [phase1-handoff.md](./phase1-handoff.md) 为准。

---

## 8. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 验收通过并固化；完成本说明；seed 固化 `demo` |
