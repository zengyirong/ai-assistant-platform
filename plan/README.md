# 规划与设计文档

本目录存放产品与设计侧文档；可执行工程契约在仓库根目录的 [`docs/`](../docs/)。

## 阅读顺序

```text
AI智能助手产品规划_V2.md
        ↓
v2-planning-review.md
        ↓
AI智能助手平台_Phase0_系统设计_V1.md
        ↓
AI智能助手平台_Phase0.5_UIUX设计_V1.md
        ↓
phase0.5-uiux-review.md
        ↓
../docs/*（DDL / API / SSE）
        ↓
M1 总结 / Bugs → … → **M6 一期收口（已完成）** → [交接说明](./phase1-handoff.md) → **M7 系统管理 / RBAC 闭环**
```

## 索引

| 文档 | 说明 |
|---|---|
| [AI智能助手产品规划_V2.md](./AI智能助手产品规划_V2.md) | 产品范围、分期、DoD |
| [v2-planning-review.md](./v2-planning-review.md) | 审查决议 R1–R6 |
| [AI智能助手平台_Phase0_系统设计_V1.md](./AI智能助手平台_Phase0_系统设计_V1.md) | 架构 / 数据 / API / ADR |
| [AI智能助手平台_Phase0.5_UIUX设计_V1.md](./AI智能助手平台_Phase0.5_UIUX设计_V1.md) | 一期 IA / 页面 / 交互 |
| [phase0.5-uiux-review.md](./phase0.5-uiux-review.md) | Phase 0.5 审查纪要（通过，带条件） |

### 里程碑（执行与复盘）

| 文档 | 说明 |
|---|---|
| [milestone-M1-bugs-and-fixes.md](./milestone-M1-bugs-and-fixes.md) | 联调 Bugs B1–B12（含 M2 收尾） |
| [milestone-M4-M5-bugs-and-fixes.md](./milestone-M4-M5-bugs-and-fixes.md) | **M4/M5 联调 Bugs B13–B14**（登录死循环 / 错误文案） |
| [milestone-M1-deep-summary.md](./milestone-M1-deep-summary.md) | 审查→真实 RAG 主路径可演示：深度总结 |
| [milestone-M2-next-goals.md](./milestone-M2-next-goals.md) | M2 目标与 DoD（已达成） |
| [milestone-M2-completion.md](./milestone-M2-completion.md) | **M2 完成说明（验收通过）** |
| [milestone-M3-next-goals.md](./milestone-M3-next-goals.md) | M3 目标与 DoD（已达成） |
| [milestone-M3-completion.md](./milestone-M3-completion.md) | **M3 完成说明（验收通过）** |
| [milestone-M4-next-goals.md](./milestone-M4-next-goals.md) | M4 目标与 DoD（已达成） |
| [milestone-M4-completion.md](./milestone-M4-completion.md) | **M4 完成说明（验收通过；含 B14 补丁说明）** |
| [milestone-M5-next-goals.md](./milestone-M5-next-goals.md) | M5 目标与 DoD（已达成） |
| [milestone-M5-completion.md](./milestone-M5-completion.md) | **M5 完成说明（验收通过）** |
| [milestone-M6-next-goals.md](./milestone-M6-next-goals.md) | M6 目标与 DoD（已达成） |
| [milestone-M6-completion.md](./milestone-M6-completion.md) | **M6 完成说明（验收通过）— 一期收口** |
| [milestone-M7-next-goals.md](./milestone-M7-next-goals.md) | **下一里程碑：系统管理 / 完整 RBAC（含菜单，无部门）** |
| [phase1-handoff.md](./phase1-handoff.md) | **一期交接 / 演示说明** |

## 与 `docs/` 的分工

| 目录 | 内容 |
|---|---|
| `plan/` | 为什么做、做什么、页面怎么组织、里程碑复盘与下一步 |
| `docs/` | 怎么落地为契约（DDL、OpenAPI、SSE） |
