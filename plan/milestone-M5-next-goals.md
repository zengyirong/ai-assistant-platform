# 里程碑 M5 — 下一目标规划（可追溯与运维增强）

> 前置：[M4 完成说明](./milestone-M4-completion.md) 已验收  
> 依据：M4 Should 遗留、产品规划 V2 §P1/P2、Phase 0 `audit_log`  
> 日期：2026-09-14  
> 状态：**进行中**

---

## 1. 一句话目标

**关键写操作可追溯，一期底座收尾可交接**：审计写入起步；不引入重型中间件，除非业务强制。

---

## 2. Must（必须）

1. **审计日志写入**
   - [x] 覆盖：文档上传 / 删除 / 重试、KB 成员变更、登录成功/失败、登出  
   - [x] 写入 `audit_log`；独立 session，失败不阻断主流程  
2. **审计只读查询（最小）**
   - [x] `GET /api/v1/audit-logs`（ADMIN）+ action / user_id 过滤  
   - [x] 前端简易表格页（`/audit/list`，authority=ADMIN）  

---

## 3. Should

- [ ] Citation / 会话边角体验小修  
- [ ] Golden Dataset 增加 1～2 条「检索离线断言」雏形  
- [ ] 系统用户创建（同 org 建 USER）薄 API  

---

## 4. Won’t

- Redis / Celery / MinIO  
- OCR、Rerank、Hybrid Search  
- 完整 CD 自动部署  
- 完整系统管理后台  

---

## 5. 退出标准

```text
☑ 上传/删文档/改成员后 audit_log 有对应记录
☑ ADMIN 可按时间查询审计列表（API + UI）
□ 主路径回归（pytest）仍绿 — 本地验收
□ plan 完成说明 — 验收后固化
```

本地验收建议：

1. 登录 admin → 侧栏「审计日志」可见登录记录  
2. 上传 / 删文档 / 改成员后再刷新，可见对应 `action`  
3. 故意输错密码 → `auth.login` + `FAILED`；Toast 为「用户名或密码错误」；**无** logout 刷屏（见 [B13/B14](./milestone-M4-M5-bugs-and-fixes.md)）

---

## 6. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 初版：M4 验收后下一里程碑（承接审计 Should） |
| 2026-09-14 | 开工：AuditLog 模型、best-effort 写入、ADMIN 列表 API/UI |
| 2026-09-14 | 联调暴露 B13/B14 已修；Bugs 归档见 `milestone-M4-M5-bugs-and-fixes.md` |
