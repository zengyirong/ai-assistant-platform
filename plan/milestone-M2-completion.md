# 里程碑 M2 — 完成说明（验收通过）

> 状态：**已完成**（2026-09-14 验收通过）  
> 目标文档：[milestone-M2-next-goals.md](./milestone-M2-next-goals.md)  
> 关联 Bugs：[milestone-M1-bugs-and-fixes.md](./milestone-M1-bugs-and-fixes.md)（B6 关闭；B9–B11 为本阶段体验修复）

---

## 1. 一句话结论

**文本型 PDF / DOCX 已可解析入库并参与真实 RAG 问答**；与 TXT/MD 共用 Job 流水线；扫描版 PDF / 旧 `.doc` 明确失败。配套修掉 Citation 文件名、按文件名优先检索、删除外键三类体验问题。

---

## 2. DoD 对照

| 退出标准 | 结果 |
|---|---|
| PDF 样例 → READY → 问答有 Citation（可含页码） | 通过（如 `提示词工程.pdf`） |
| DOCX 样例 → READY → 同上 | 通过（如 `书籍.docx`） |
| TXT/MD 回归 | 通过 |
| 不支持类型/损坏文件有明确原因 | 通过（扫描件、加密 PDF、旧 `.doc`） |
| 真实 Embedding 批次限制 + 本机 Qdrant 路径仍可用 | 通过 |
| plan 完成说明 | 本文 |

---

## 3. 技术落地摘要

| 项 | 说明 |
|---|---|
| PDF | PyMuPDF（`pymupdf`），按页抽文本，chunk 带 `page` |
| DOCX | `python-docx`，段落 / Heading section / 表格 |
| 入口 | `app.ai.parser.parse_document_bytes` |
| 流水线 | `parse → chunk(元数据) → embed → index` |
| 依赖 | `backend/pyproject.toml`：`pymupdf`、`python-docx` |
| 单测 | `tests/unit/test_parsers.py` |

### 明确不做（仍有效）

- OCR / 扫描版 PDF  
- 旧 Word `.doc`  
- 复杂版式、表格结构化理解  

---

## 4. 验收同期体验修复（建议一并视为 M2 收尾）

| ID | 内容 | 状态 |
|---|---|---|
| B6 | DOCX「一期不支持」 | **关闭**（已实现） |
| B9 | Citation 显示文件名 | 已修复 |
| B10 | 问题含完整文件名时优先检索该文档 | 已增强 |
| B11 | 删除曾被引用的文档外键报错 | 已修复 |
| — | `RetrievedChunk` 误删导致后端起不来 / 前端 502 白屏 | 已修复 |

---

## 5. 已知限制（带入后续）

1. 语义检索仍可能召回主题相近的其他文档（无文件名时）  
2. `message_citation.document_id/chunk_id` DDL 仍无 `ON DELETE CASCADE`，靠应用层先删引用  
3. Citation 正文角标 `[1][2]` 依赖模型输出，侧栏为准  
4. Alembic / CI / Golden Dataset 未做 → **M3**

---

## 6. 建议 commit 范围（若尚未提交体验修复）

见会话中给出的：

```text
fix: Citation 文件名展示、按文件名优先检索与文档删除外键
```

M2 解析本体若已提交（`feat: 实现 PDF/DOCX 解析…`），本文档可随「固化文档」单独提交。

---

## 7. 下一步

→ **[里程碑 M3 — 工程化](./milestone-M3-next-goals.md)**：Alembic、CI、核心回归、Golden Dataset 起步。

---

## 8. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-09-14 | 验收通过；完成本说明 |
