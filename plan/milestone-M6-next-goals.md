# 里程碑 M6 — 下一目标规划（一期收口）

> 前置：[M5 完成说明](./milestone-M5-completion.md) 已验收  
> 依据：产品规划 V2 §P1 余量、M5 Should、一期 DoD「可交接」  
> 日期：2026-09-14  
> 状态：**进行中**

---

## 1. 一句话目标

**宣布一期底座可交接**：补齐轻量缺口（建 USER + Golden），写清演示与运维说明；不膨胀进 P2 / 完整系统管理。

---

## 2. Must（必须）

1. **一期交接说明**（文档）→ [`phase1-handoff.md`](./phase1-handoff.md)
2. **回归确认** → `ruff` + `pytest`

---

## 3. Should（本里程碑已选）

- [x] 同 org 创建 USER 薄 API（`POST /api/v1/users`，ADMIN）
- [x] Golden Dataset：离线 keyword 排序断言 + 多样本
- [ ] Citation / 会话边角小修（未选，结转后续）

---

## 4. Won’t

- 完整系统管理后台（组织/角色/菜单全套）— 若要做，另立里程碑  
- Redis / Celery / MinIO / OCR / Rerank / Hybrid Search（规划 P2）  
- 完整 CD 自动部署  

---

## 5. 退出标准（草案）

```text
☑ 交接/演示说明落盘（plan/phase1-handoff.md）
□ 主路径回归通过
☑ （可选）选定的 Should 项完成
□ plan 完成说明
```

---

## 6. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 初版：M5 验收后的一期收口里程碑 |
| 2026-09-14 | 启动：handoff + USER create + Golden 增强 |
