# 里程碑 M2 — 下一目标规划

> 状态：**目标已达成（见 [完成说明](./milestone-M2-completion.md)）**  
> 前置： [M1 阶段总结](./milestone-M1-deep-summary.md) 已达成「真实 RAG 主路径可演示」  
> 依据：产品规划 V2 P0/P1、Phase 0 设计、Phase 0.5 UI、M1 Bugs 遗留项  
> 日期：2026-09-14

---

## 1. M2 一句话目标

**补齐办公文档解析（PDF/DOCX），使上传区承诺的格式真正可用，并保持真实 RAG 主路径稳定可回归。**

成功时用户感知：

```text
上传 PDF 或 DOCX → 解析成功（READY）→ 问答能引用到文档内容（含页码若可得）
```

---

## 2. 为什么是 M2（优先级论证）

| 候选 | 为何不作为 M2 主目标 |
|---|---|
| 系统管理（用户/角色/空间） | 无阻塞主路径；后端 API 未齐；Phase 0.5 已决议暂缓 |
| Alembic / CI / 审计 | 重要但属工程化，不增加「能答更多真实材料」的产品能力 |
| Chat 角标 [1][2]、高保真 | 增强项；侧栏 Citation 已满足一期交互优先 |
| 换 Chroma / 上云向量库 | 与 M1 结论冲突：Embedding 与库无强绑定，无迁移必要 |

**P0 最大缺口仍是 Parser（PDF/DOCX）。** 规划里 Parser 与 Document 同属必须项；UI 已展示格式支持，能力缺口会造成信任问题。

---

## 3. M2 范围

### 3.1 Must（必须完成）

1. **PDF 解析**
   - 抽取纯文本（按页更佳）
   - 进入现有 Job：PARSE → CHUNK → EMBED → INDEX  
   - 失败有明确 `error_code` / 用户可读原因  
2. **DOCX 解析**
   - 抽取正文文本（段落级即可）
   - 同上流水线与失败语义  
3. **与现有 RAG 对齐**
   - Citation 尽量带 `page`（PDF）；DOCX 可用 section/段落信息  
   - 不破坏 TXT/MD 路径；真实 Embedding 批次限制继续有效  
4. **验收用例**
   - 至少各 1 份真实 PDF、DOCX 走通 READY + 问答命中  
   - 回归：TXT/MD 仍 READY；Qdrant/代理相关修复不回退  
5. **文档**
   - 更新本目录：解析依赖、限制（扫描版 PDF/OCR 不做）、已知问题  
   - Bugs 有新项则追加到 M1 Bugs 文档或新建 M2 Bugs 节

### 3.2 Should（尽量做，可裁剪）

- 解析进度更细（job.progress 与 UI 文案）  
- 前端错误码映射（格式错误 vs 依赖错误）  
- 超大页数/空文本的校验与提示  
- 简单集成测试：mock 解析器或夹具文件（不强制打真实百炼）

### 3.3 Won’t（明确不做，防膨胀）

- OCR / 扫描件 PDF  
- 复杂版式还原、表格结构化理解  
- MinIO 替换本地磁盘  
- Celery/Redis 异步集群化（可先同步/后台 task 现状）  
- 完整用户管理与审计中心  
- 换向量库产品（Chroma 等）

---

## 4. 建议技术取向（执行时再拍板）

| 格式 | 候选方向 | 注意 |
|---|---|---|
| PDF | `pymupdf`（fitz）或 `pypdf` | 优先可维护、页码可得；加密 PDF 明确失败 |
| DOCX | `python-docx` | 目录/页眉页脚策略写清；老 `.doc` 可不支持 |

原则：

- 解析结果写入现有 `document_chunk` 真源，再走平台 Embedding  
- 解析器失败 **不要** 误报成向量库错误  
- 依赖写入 `pyproject.toml`，在 README/本规划注明系统库需求（若有）

---

## 5. 退出标准（DoD）

同时满足才算 M2 完成：

```text
□ PDF 样例上传 → READY → 相关问题能答出并有 Citation
□ DOCX 样例上传 → READY → 同上
□ TXT/MD 回归通过
□ 不支持的类型/损坏文件：明确失败原因（非模糊 INTERNAL_ERROR）
□ 真实 Embedding（批次≤10）与本机 Qdrant（trust_env=False）路径仍可用
□ plan 中有 M2 完成说明或测试记录更新
```

---

## 6. 建议执行顺序

```text
1. 选定 PDF/DOCX 库并加依赖
2. 实现 parser 接口（与现有 txt/md 并列）
3. 单测：夹具文件 → chunks
4. 接通 Job pipeline；手工上传验收
5. Citation page/section 字段对齐
6. 前端文案：区分「解析中 / 格式不支持 / 依赖失败」
7. 回归 Chat + 写简短测试记录
```

预估粒度（供排期，非承诺）：**1 个小迭代**（视 PDF 样例复杂度浮动）。

---

## 7. M2 之后的预告（不纳入本里程碑）

便于对齐长期规划，避免 M2 做完迷失：

| 顺序建议 | 主题 | 来源 |
|---|---|---|
| M3 | 工程化：Alembic 唯一迁移、CI、核心 API/集成测试、Golden Dataset 起步 | 规划 P1 |
| M4 | 体验与治理：用户列表/加成员体验、审计日志、错误文案体系、上传进度 | Phase 0.5 + P1 |
| 更后 | Redis/Celery、MinIO、OCR、Rerank、Hybrid Search | 规划 P2 |

**补充：** 若业务强制「先多用户协作再上 PDF」，可将「用户搜索 + 成员体验」插成 **M2.5**，但不应替换 PDF/DOCX 作为默认下一刀。

---

## 8. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 扫描版 PDF 用户期望可解析 | Won’t 写清；UI 提示「仅文本型 PDF」 |
| 解析慢导致同步请求超时 | 保持 Job 异步；必要时调超时与进度 |
| 依赖体积/许可证 | 选型时记录；锁版本 |
| 真模型费用 | 开发默认可用 fake；CI 不调用付费 API |
| 密钥与代理老问题复发 | 沿用 M1 Bugs 约定；Runbook 检查 `/ready` |

---

## 9. 与现有文档的衔接

| 文档 | 关系 |
|---|---|
| 产品规划 V2 §P0 Parser | M2 直接还债 |
| Phase 0 设计 Document/Job | 扩展 parser，不改总体流水线 |
| Phase 0.5 上传文案 PDF/DOCX/TXT/MD | M2 使文案与能力一致 |
| M1 Bugs B6 | 在 M2 关闭 |

---

## 10. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 初版：M2 目标、范围、DoD、后续预告 |
| 2026-09-14 | 开始实现：PyMuPDF + python-docx 解析器接入 Job 流水线 |
| 2026-09-14 | **验收通过** → [milestone-M2-completion.md](./milestone-M2-completion.md)；下一里程碑见 M3 |
