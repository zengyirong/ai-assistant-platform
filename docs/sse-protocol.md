# SSE Protocol V1

> 依据：Phase 0 §9–10  
> 配套：[`api.md`](./api.md)（HTTP 错误码与 Chat 入口）

---

## 1. 端点

```text
POST /api/v1/chat/stream
Authorization: Bearer <jwt>
Content-Type: application/json
Accept: text/event-stream
```

请求体见 `api.md` / OpenAPI `ChatStreamRequest`。

流建立前完成鉴权与 KB 数据权限校验；失败返回普通 JSON Error Envelope（非 SSE）。

---

## 2. 传输格式

每个 SSE 事件：

```text
data: <json>\n\n
```

一期可不使用 SSE `event:` 字段名；业务事件类型放在 JSON 的 `event` 字段。

统一包：

```json
{
  "version": "1.0",
  "event": "text",
  "request_id": "req_xxx",
  "conversation_id": "conv_xxx",
  "message_id": "msg_xxx",
  "seq": 2,
  "data": {}
}
```

| 字段 | 说明 |
|---|---|
| `version` | 协议版本，一期固定 `1.0` |
| `event` | 见下表 |
| `request_id` | 与 HTTP / 审计一致 |
| `conversation_id` | 会话 ID |
| `message_id` | 本轮 ASSISTANT 消息 ID |
| `seq` | 从 1 起严格单调递增 |
| `data` | 事件载荷 |

---

## 3. 一期事件

| event | 时机 | data |
|---|---|---|
| `start` | 流开始 | `{ "status": "GENERATING" }` |
| `text` | token / 文本增量 | `{ "content": "..." }`（增量拼接） |
| `citation` | 检索结果确定后（可在 text 前或中） | `{ "citations": [ Citation ] }` |
| `done` | 正常结束 | `{ "status": "COMPLETED", "finish_reason": "stop" }` |
| `error` | 失败结束 | `{ "code": "LLM_TIMEOUT", "message": "..." }` |

Citation 项：

```json
{
  "document_id": "doc_1",
  "document_name": "员工手册.pdf",
  "chunk_id": "chunk_12",
  "page": 12,
  "section": "年假制度",
  "score": 0.86,
  "snippet": "……"
}
```

无可靠依据时：

```text
可发 citation（空数组）或跳过
text 内容为拒答固定话术
done
```

拒答文案：`当前知识库中未找到可靠依据。`

---

## 4. 协议规则

1. `seq` 严格单调递增；客户端可检测空洞但不强制重连补齐一期。  
2. `error` 之后不得再发 `done` 或其它业务事件。  
3. `done` 之后不得再发任何业务事件。  
4. 未知 `event`：前端忽略（向前兼容二期 `metric` / `risk` 等）。  
5. `request_id` 贯穿 API、日志、审计、SSE。  
6. 正常完成：`message.status = COMPLETED`，并持久化 citations。  
7. 客户端 Abort：`message.status = ABORTED`；尽量停止上游 LLM；**禁止**之后再标 `COMPLETED`。  
8. 服务端失败：`message.status = FAILED`，发 `error` 事件。

推荐顺序：

```text
start
  → citation? 
  → text* 
  → done
```

或：

```text
start → text* → citation → done
```

一期推荐：**先 citation 再 text**，便于 UI 先展示依据。

---

## 5. Abort

```text
AbortController.abort()
  → 连接断开
  → FastAPI 感知 disconnect
  → 停止上游 stream
  → message.status = ABORTED
```

无独立 `POST /chat/abort`（一期）。

审计可记 `SSE_CLIENT_ABORTED`（不必作为 HTTP body）。

---

## 6. TypeScript 类型（前端契约草案）

```ts
export type SseEventName = 'start' | 'text' | 'citation' | 'done' | 'error';

export interface SseEnvelope<T = unknown> {
  version: '1.0';
  event: SseEventName;
  request_id: string;
  conversation_id: string;
  message_id: string;
  seq: number;
  data: T;
}

export interface SseCitationItem {
  document_id: string;
  document_name?: string | null;
  chunk_id: string;
  page?: number | null;
  section?: string | null;
  score?: number | null;
  snippet?: string | null;
}
```

后端对应使用 Pydantic model（脚手架时落 `backend/app/schemas/sse.py`）。

---

## 7. 测试要点

- 事件顺序与 `seq`  
- `error` 后无 `done`  
- Abort 后状态为 `ABORTED`  
- 无依据拒答 + `done`  
- 未知 event 可忽略  
