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
【里程碑】M1 总结 / Bugs → M2 下一目标
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
| [milestone-M1-bugs-and-fixes.md](./milestone-M1-bugs-and-fixes.md) | M1 联调 Bugs、根因、修复与验收清单 |
| [milestone-M1-deep-summary.md](./milestone-M1-deep-summary.md) | 审查→真实 RAG 主路径可演示：深度总结 |
| [milestone-M2-next-goals.md](./milestone-M2-next-goals.md) | 下一里程碑：PDF/DOCX 解析目标与 DoD |

## 与 `docs/` 的分工

| 目录 | 内容 |
|---|---|
| `plan/` | 为什么做、做什么、页面怎么组织、里程碑复盘与下一步 |
| `docs/` | 怎么落地为契约（DDL、OpenAPI、SSE） |
