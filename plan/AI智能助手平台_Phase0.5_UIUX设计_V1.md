# AI 智能助手平台 — Phase 0.5 UI/UX 设计 V1

> 阶段：Phase 0.5 / Product & Interaction Design  
> 范围：一期「文档 RAG 智能查询助手」  
> 前端基座：Vben Admin 5 + Vue3 + TypeScript + Element Plus  
> 目标：在进入正式前端开发前，固定一期核心页面的信息架构、用户流程、低保真布局、页面状态、权限与交互规则。

---

# 1. 为什么需要 Phase 0.5

当前 Phase 0 已覆盖系统架构、RBAC、数据模型、API、SSE、Docker、测试和工程规范，主要回答“系统怎么实现”。

Phase 0.5 主要回答：

- 用户进入系统后看到什么
- 用户如何完成核心任务
- 页面如何组织
- Drawer / Dialog / 独立页面如何选择
- Loading / Empty / Error / Success 如何表现
- 不同权限用户能看到和操作什么

如果缺少这一层，开发阶段容易出现页面边写边改、状态文案不一致、权限逻辑只存在代码里、AI Chat 与后台 CRUD 风格混杂等问题。

---

# 2. 一期信息架构 IA

推荐一级菜单：

```text
AI 智能助手
│
├── 智能问答
│
├── 知识库
│   └── 知识库管理
│
└── 系统管理
    ├── 用户管理
    ├── 角色管理
    ├── 菜单管理
    ├── 空间管理
    └── 审计日志
```

> M7 起「菜单管理」纳入 IA，用于完整 RBAC（用户→角色→菜单/权限）；**不含部门**（协作边界仍为 Space）。详见 [milestone-M7-next-goals.md](./milestone-M7-next-goals.md)。

不建议把文档管理、成员管理、RAG 配置、解析任务全部提升为左侧一级菜单，它们属于某个知识库内部的子能力。

---

# 3. 页面关系

```text
知识库列表
    │
    ├── 新建知识库 Drawer
    │
    └── 知识库详情
           │
           ├── 概览
           ├── 文档
           ├── 成员与权限
           └── RAG 配置

智能问答
    │
    ├── 会话列表
    ├── 知识库选择
    ├── Chat
    └── Citation 来源侧栏
```

核心边界：

```text
知识库管理 = 管理知识
智能问答   = 使用知识
```

---

# 4. 知识库列表页

## 4.1 页面目标

用户可以：

- 查看有权限访问的知识库
- 搜索知识库
- 按可见范围 / 状态筛选
- 创建知识库
- 进入知识库详情
- 编辑 / 删除知识库

## 4.2 推荐布局

```text
┌──────────────────────────────────────────────────────────────┐
│ 知识库管理                                  [ + 新建知识库 ] │
│                                                              │
│ [名称搜索           ] [可见范围▼] [状态▼] [查询] [重置]     │
├──────────────────────────────────────────────────────────────┤
│ 名称        可见范围   文档数   状态    Owner    更新时间  操作 │
│                                                              │
│ HR制度库     空间        28      正常    张三     ...      详情 │
│ 医疗知识库   私有        15      正常    李四     ...      详情 │
│ 产品文档     空间        43      正常    王五     ...      详情 │
└──────────────────────────────────────────────────────────────┘
```

一期优先使用 Table，因为后期会有搜索、筛选、排序、状态、权限和批量能力。

---

# 5. 新建知识库

推荐使用 Drawer。

字段：

```text
名称 *
描述
可见范围 *
所属空间
```

Wireframe：

```text
┌────────────── 新建知识库 ──────────────┐
│ 名称 *                                │
│ [ HR 人事制度知识库                 ] │
│                                       │
│ 描述                                  │
│ [                                  ]  │
│                                       │
│ 可见范围 *                            │
│ (●) 私有                              │
│ ( ) 空间                              │
│                                       │
│ 所属空间                              │
│ [ 默认空间 ▼ ]                        │
│                                       │
│              [取消]      [创建]       │
└───────────────────────────────────────┘
```

一期创建知识库时不要暴露 `chunk_size / overlap / top_k / threshold / temperature` 等高级参数。

---

# 6. 知识库详情页

推荐独立页面 + Tabs：

```text
知识库 / HR 人事制度知识库

HR 人事制度知识库
用于存放员工手册、考勤、请假、福利制度

[空间] [正常]                                  [编辑]

------------------------------------------------------------

[概览] [文档] [成员与权限] [RAG 配置]

------------------------------------------------------------
```

---

# 7. 概览 Tab

一期保持简洁：

```text
┌────────────┐ ┌────────────┐ ┌────────────┐
│ 文档数量    │ │ 可用 Chunk │ │ 解析失败    │
│     28     │ │   1,356    │ │      2     │
└────────────┘ └────────────┘ └────────────┘
```

再展示最近文档和基本信息：

```text
最近文档
员工手册.pdf          READY
考勤制度.docx         READY
2026福利制度.pdf      PROCESSING
```

基本信息包括创建人、创建时间、更新时间、所属空间、可见范围、知识库状态。

---

# 8. 文档 Tab

这是一期最核心的业务页面之一。

```text
文档                                      [上传文档]

支持 PDF / DOCX / TXT，单文件最大 20MB

----------------------------------------------------------------

文件名          类型   大小   状态        进度    上传人    操作

员工手册.pdf    PDF    3MB   ● 已就绪     100%    admin    删除
制度.docx       DOCX   1MB   ◌ 解析中      65%     admin    -
福利.pdf        PDF    5MB   × 解析失败    -       admin    重试 删除
```

---

# 9. 文档状态设计

后端状态：

```text
UPLOADED
PROCESSING
READY
FAILED
DELETED
```

用户文案：

| 状态 | 展示 |
|---|---|
| UPLOADED | 已上传 |
| PROCESSING | 解析中 |
| READY | 已就绪 |
| FAILED | 解析失败 |
| DELETED | 一般不展示 |

Job 细状态：

```text
PENDING → 排队中
PARSING → 正在解析
CHUNKING → 正在切分
EMBEDDING → 正在生成向量
INDEXING → 正在建立索引
SUCCESS → 处理完成
FAILED → 处理失败
```

---

# 10. 解析失败交互

```text
福利.pdf    解析失败    [查看原因] [重试] [删除]
```

点击查看原因：

```text
解析失败

错误类型：
PDF_ENCRYPTED

原因：
该 PDF 已加密，当前无法解析。

建议：
请上传解除密码后的 PDF 文件。
```

原则：

```text
技术错误码 + 用户可理解原因 + 下一步建议
```

---

# 11. 上传文档

一期推荐 Dialog。

```text
┌──────────────── 上传文档 ────────────────┐
│           拖拽文件到这里                 │
│                 或                      │
│              [选择文件]                  │
│                                         │
│ PDF / DOCX / TXT，单文件 ≤ 20MB         │
│                                         │
│ 员工手册.pdf             等待上传         │
│ 福利制度.pdf             等待上传         │
│                                         │
│                         [开始上传]        │
└─────────────────────────────────────────┘
```

必须区分：

```text
上传成功 ≠ 文档可问答
```

正确流程：

```text
上传成功 → 正在解析 → 正在切分 → 生成向量 → 已就绪
```

上传完成提示建议：

> 上传成功，文档正在后台解析。

---

# 12. 成员与权限 Tab

Private KB：

```text
当前知识库为私有知识库
仅创建人及被显式授权的成员可以访问。
```

Space KB：

```text
所属空间：默认空间

用户          权限
张三          Owner
李四          Editor
王五          Viewer
```

一期建议规则：

```text
Space 成员默认 Viewer
KnowledgeBase Member 可提升为 Editor / Owner
```

权限语义：

```text
Viewer → 查看 / 问答
Editor → Viewer + 上传 / 删除文档 / 编辑部分设置
Owner  → Editor + 成员管理 / 删除 KB / 高级配置
```

---

# 13. RAG 配置 Tab

一期建议仅 `ADMIN / KB OWNER` 可见。

```text
检索设置

Chunk 策略
[Recursive ▼]

Chunk Size
[800]

Chunk Overlap
[120]

Top K
[5]

相似度阈值
[使用平台默认]

--------------------------------

生成设置

模型
[qwen-plus ▼]

Temperature
[0.2]

System Prompt
[................................]

                                   [保存]
```

推荐用“基础设置 / 高级设置”折叠，高级参数默认隐藏。

---

# 14. 智能问答页面

智能问答应独立于知识库详情。

```text
┌─────────────┬───────────────────────────────┬───────────────┐
│ 会话         │ 当前知识库                    │ 引用来源       │
│             │ [HR制度库 ×] [产品库 ×]       │               │
│ + 新会话     │                               │ 员工手册.pdf   │
│             │         Chat Message          │ P12           │
│ 会话 1       │                               │               │
│ 会话 2       │         AI Response           │ 请假制度.docx  │
│             │                               │ P3            │
│             │ [请输入问题................]   │               │
└─────────────┴───────────────────────────────┴───────────────┘
```

---

# 15. Chat 组件划分

```text
AiChatPage
├── ConversationSidebar
├── KnowledgeScopeSelector
├── ChatMessageList
│   ├── UserMessage
│   └── AssistantMessage
├── ChatInput
└── CitationPanel
```

避免把所有逻辑堆到一个 `ChatPage.vue`。

---

# 16. Citation 交互

回答正文中：

```text
根据员工手册，公司正式员工每年享有……
[1] [2]
```

点击来源后右侧展示：

```text
员工手册.pdf
第 12 页
年假制度

“正式员工工作满一年后……”
```

至少展示：

```text
document_name
page
section
snippet
```

`score` 可只给管理员或调试模式查看。

---

# 17. SSE UI 状态

```text
IDLE
  ↓
SENDING
  ↓
STREAMING
  ├── COMPLETED
  ├── ABORTED
  └── ERROR
```

SENDING：

```text
正在思考…
```

STREAMING：

```text
持续追加文本
[停止生成]
```

ABORTED：

```text
生成已停止
```

ERROR：

```text
回答生成失败
[重新生成]
```

---

# 18. 空状态

知识库为空：

```text
暂无知识库
创建第一个知识库，上传文档后即可开始智能问答。
[创建知识库]
```

文档为空：

```text
当前知识库还没有文档
支持 PDF / DOCX / TXT
[上传文档]
```

Chat 无会话：

```text
开始你的第一次知识问答
请选择知识库并输入问题。
```

---

# 19. Loading 设计

不要所有页面都使用全屏 Spin。

推荐：

```text
Table → Skeleton / Loading
Document Job → Progress / Status
Chat → Streaming
Drawer Submit → Button Loading
```

---

# 20. 删除交互

删除知识库时必须说明影响：

```text
删除知识库「HR 人事制度知识库」？

删除后：
- 知识库无法继续访问
- 关联文档将被删除
- 关联向量索引将被清理

该操作不可恢复。
```

删除文档：

```text
删除「员工手册.pdf」？
删除后该文档将不再参与知识检索。
```

---

# 21. 权限 UI

按钮权限：

```text
knowledge:create
knowledge:update
knowledge:delete

document:upload
document:delete
document:retry
```

原则：

- 无权限的高频操作可以隐藏
- 因资源状态不可操作时用 disabled
- disabled 必须能解释原因

---

# 22. 后端状态与前端文案映射

不要在页面中散落状态判断。

推荐统一映射：

```ts
const DOCUMENT_STATUS_MAP = {
  UPLOADED: { label: '已上传' },
  PROCESSING: { label: '解析中' },
  READY: { label: '已就绪' },
  FAILED: { label: '解析失败' },
}
```

后端状态保持稳定，前端负责产品文案。

---

# 23. 页面交互规则

```text
轻量创建 / 编辑 → Drawer
二次确认         → Dialog
复杂管理页面     → 独立 Route
辅助信息         → Drawer / Side Panel
```

一期对应：

```text
新建知识库 → Drawer
删除确认   → Dialog
知识库详情 → Route
Citation   → Right Panel
上传文档   → Dialog
```

---

# 24. 响应式策略

一期主要面向 Desktop 企业后台，优先：

```text
1440px
1920px
```

不要求一期完整适配手机端。

Chat 小屏时：

- 会话侧栏可折叠
- Citation 侧栏可改 Drawer

---

# 25. UI 技术职责

```text
Vben Admin 5
├── Layout
├── Router
├── Menu
├── Tabs
├── KeepAlive
└── RBAC

Element Plus
├── Form
├── Input
├── Select
├── Drawer
├── Dialog
├── Upload
├── Table
└── Pagination

VXE Table
└── 后期复杂表格

自研 AI Components
├── ChatMessage
├── ChatInput
├── CitationPanel
├── StreamingText
├── KnowledgeScopeSelector
└── SourceCard
```

---

# 26. 一期核心用户流程

创建知识库：

```text
知识库列表
→ 新建知识库
→ 填写名称 / 范围 / Space
→ 创建
→ 进入详情
```

上传文档：

```text
知识库详情
→ 文档 Tab
→ 上传文档
→ 上传成功
→ PROCESSING
→ READY
```

开始问答：

```text
智能问答
→ 选择知识库
→ 输入问题
→ SSE Streaming
→ 回答
→ Citation
```

解析失败：

```text
Document FAILED
→ 查看失败原因
→ 修正文档 / Retry
→ 重新处理
```

---

# 27. 建议的 UI 文档目录

```text
docs/ui/
├── information-architecture.md
├── user-flow.md
├── knowledge-base-wireframe.md
├── chat-wireframe.md
├── ui-state-spec.md
└── interaction-spec.md
```

当前这份文档可以作为 V1 合并稿，后续再拆分。

---

# 28. Phase 0.5 退出标准

- [x] 一级菜单结构
- [x] 知识库列表布局
- [x] 新建 KB 交互
- [x] KB 详情 Tabs
- [x] 文档列表与状态
- [x] 上传交互
- [x] 失败 / Retry
- [x] 成员权限页面
- [x] RAG 配置页
- [x] Chat 三栏布局
- [x] Citation 交互
- [x] SSE 状态
- [x] Empty / Loading / Error
- [x] Drawer / Dialog / Route 规则
- [ ] 高保真 UI 稿（可选）
- [ ] Figma / Pencil 实际视觉稿（可选）
- [ ] 前端组件 props / emits 详细规范
- [ ] API 与 UI 字段映射表

---

# 29. 最终结论

Phase 0 解决：

> 系统如何设计。

Phase 0.5 解决：

> 产品如何被用户使用。

一期真正开始编码之前，至少应该具备：

```text
Architecture
+
Data Model
+
API
+
UI/UX
+
Interaction
+
Test Strategy
```

知识库一期最核心的 UI 主线：

```text
管理知识 → Knowledge Base
处理知识 → Document Pipeline
使用知识 → AI Chat
```

三者职责明确、状态统一、权限一致，才能形成完整的 AI 智能助手产品体验。
