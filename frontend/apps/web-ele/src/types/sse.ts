/** SSE Protocol V1 — see docs/sse-protocol.md */

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

export interface SseTextData {
  content: string;
}

export interface SseCitationData {
  citations: SseCitationItem[];
}

export interface SseDoneData {
  status: 'COMPLETED';
  finish_reason?: string;
}

export interface SseErrorData {
  code: string;
  message: string;
}
