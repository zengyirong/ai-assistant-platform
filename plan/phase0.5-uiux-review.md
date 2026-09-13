# Phase 0.5 UI/UX 审查纪要

> 对象：[AI智能助手平台_Phase0.5_UIUX设计_V1.md](./AI智能助手平台_Phase0.5_UIUX设计_V1.md)  
> 日期：2026-09-13  
> 结论：**通过（带条件）** — 可进入前端业务页编码

---

## 1. 总评

文档把「管理知识 / 处理文档 / 使用问答」拆清楚，线框、状态文案、Drawer/Dialog/Route 规则与现有 Phase 0 / 后端主链路对齐，**足以指导一期前端开发**。高保真稿可选，不阻塞。

---

## 2. 非阻塞问题（执行时注意）

| ID | 项 | 说明 | 执行策略 |
|---|---|---|---|
| U1 | 系统管理菜单偏大 | IA 含用户/角色/空间/审计；后端尚无对应管理 API（Space 仅契约、审计为 P1） | **一期菜单先隐藏系统管理**；或只放占位「即将上线」 |
| U2 | 列表筛选 API | UI 有名称/可见范围/状态筛选；当前 `GET /knowledge-bases` 仅分页 | 一期前端本地过滤，或随后补 query |
| U3 | 概览统计 | 「可用 Chunk / 解析失败」无聚合接口 | 概览先做文档数 + 最近文档；统计可后补 |
| U4 | Owner 展示 | DTO 仅有 `created_by` UUID | 列表先显示 ID 截断或「—」，后续再补昵称 |
| U5 | RAG 配置权限 | UI：ADMIN/OWNER；API：`knowledge:update` + EDIT（含 EDITOR） | UI 按 OWNER/ADMIN 收敛；与 API 不一致时以后端为准并备注 |
| U6 | 上传格式 | UI 写 PDF/DOCX/TXT；后端另支持 `md` | 文案改为 PDF / DOCX / TXT / MD |
| U7 | 正文角标 [1][2] | SSE 未必注入角标 | Citation **侧栏优先**；角标为增强项 |
| U8 | `docs/ui/` 拆分建议 | 文件已在 `plan/` | 保持 `plan/` 合并稿即可，不必马上拆 |

---

## 3. 已对齐且可直接做的部分

- 知识库列表 / 新建 Drawer / 详情 Tabs  
- 文档列表、状态映射、上传 Dialog、失败 Retry  
- Chat 三栏 + Citation Panel + SSE 状态机  
- Empty / Loading / 删除确认文案  

---

## 4. 建议执行顺序（前端）

```text
1. 菜单：智能问答 + 知识库管理（系统管理暂缓）
2. api/knowledge + 知识库列表 + 新建 Drawer
3. 知识库详情（文档 Tab 优先）
4. 上传 / 状态轮询 / Retry
5. 成员 + RAG 配置
6. Chat 三栏 + SSE + Citation
```

---

## 5. 退出标准对照

文档 §28 已勾核心项；未勾的高保真 / Figma / props 规范 / 字段映射表均为可选，**不阻塞开干**。
