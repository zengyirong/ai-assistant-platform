# 里程碑 M7 — 完成说明（验收通过）

> 状态：**已完成**（2026-09-15 验收通过并固化）  
> 目标文档：[milestone-M7-next-goals.md](./milestone-M7-next-goals.md)  
> 前置：[M6 完成说明](./milestone-M6-completion.md)  
> 交接入口：[phase1-handoff.md](./phase1-handoff.md)

---

## 1. 一句话结论

**系统管理面与完整 RBAC 闭环已落地**：统一 `sys_permission`（MENU / BUTTON / API），无部门；`accessMode=backend` + `/menu/all`；用户/角色/菜单/空间/审计可管；BUTTON 与 Citation 角标小修一并收口。

---

## 2. DoD 对照

| 退出标准 | 结果 |
|---|---|
| ADMIN 可管理本 org 用户、角色、菜单权限树 | 通过 |
| 角色变更后菜单与 API 权限一致（重登/刷权限） | 通过（MENU 勾选自动扩 API + 子 BUTTON） |
| 无部门相关 UI/API/表 | 通过 |
| 空间管理页可用；审计在系统管理下 | 通过 |
| 自动化测试覆盖关键 Admin API；plan 完成说明 | 通过（`pytest` **29 passed**） |

---

## 3. 技术落地摘要

| 项 | 说明 |
|---|---|
| Schema | Alembic `20260915_0003`：`sys_permission` 增 path/component/icon/sort_order/visible/status/redirect |
| 菜单种子 | `scripts/seed_menus.py` + `docs/mysql/seed_menus_v1.sql`（MENU + BUTTON） |
| Admin API | users / roles / permissions / menu/all；space 管理页对接已有 API |
| 前端 | `/system/user\|role\|menu\|space\|audit`；`accessMode=backend`（`main.ts` 强制） |
| MENU→API | `role/service._expand_menu_related_apis` + `_MENU_API_EXPAND` |
| BUTTON | `btn:system:user:create`、`btn:knowledge:create`；`v-access:code` 显隐 |
| Citation | 正文 `[n]` 可点；无角标时补芯片；移动端点消息开 Drawer；ABORTED 文案；FakeLLM 输出编号 |
| 契约 | `docs/api.md` Admin / menu 端点已列 |

### 明确不做（仍有效）

- 部门 / 组织树 / 多租户 Organization CRUD  
- 完整动态热插拔路由  
- Redis / Celery / MinIO / OCR（P2）  

---

## 4. Should 完成情况

| 项 | 结果 |
|---|---|
| BUTTON 1～2 处落地 | **已做**：新增用户、新建知识库 |
| 菜单拖拽排序 | **未做**（保留数字 `sort_order`） |
| Citation 小修（M6 结转） | **已做** |

---

## 5. 演示账号（seed）

| 用户 | 密码 | 角色 | 侧栏差异 |
|---|---|---|---|
| `admin` | `Admin@123456` | ADMIN | 含系统管理；可见 BUTTON |
| `demo` | `Demo@123456` | USER | 工作台 / 问答 / 知识库；无系统管理；无建库按钮 |

---

## 6. 建议 commit

```text
feat(m7): BUTTON 权限与 Citation 角标；固化 M7 完成说明
```

---

## 7. 下一步（可选，勿默认膨胀）

1. **P2**：Redis / Celery / MinIO / OCR / Rerank / Hybrid Search  
2. 菜单拖拽排序、更多 BUTTON 覆盖面  
3. 二期领域能力（医院等）按产品规划另立里程碑  

日常演示与交接仍以 [phase1-handoff.md](./phase1-handoff.md) 为准；系统管理以本文 + M7 目标文档为准。

---

## 8. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-15 | 验收通过并固化；BUTTON + Citation 收口；完成本说明 |
