import type {
  ChatMessage,
  ChatStreamPayload,
  Conversation,
  ConversationPage,
  MessagePage,
} from '#/types/conversation';
import type { SseEnvelope } from '#/types/sse';

import { requestClient } from '#/api/request';
import { createSseLineParser } from '#/utils/sse-parser';

export async function listConversationsApi(params?: {
  page?: number;
  page_size?: number;
}) {
  return requestClient.get<ConversationPage>('/conversations', { params });
}

export async function createConversationApi(data?: {
  title?: string | null;
  kb_ids?: string[] | null;
}) {
  return requestClient.post<Conversation>('/conversations', data ?? {});
}

export async function getConversationApi(id: string) {
  return requestClient.get<Conversation>(`/conversations/${id}`);
}

export async function deleteConversationApi(id: string) {
  return requestClient.delete(`/conversations/${id}`);
}

export async function listMessagesApi(
  conversationId: string,
  params?: { page?: number; page_size?: number },
) {
  return requestClient.get<MessagePage>(
    `/conversations/${conversationId}/messages`,
    { params },
  );
}

export interface ChatStreamHandlers {
  onEvent: (envelope: SseEnvelope) => void;
  onEnd?: () => void;
  signal?: AbortSignal;
}

/** POST /chat/stream — raw SSE; parse via createSseLineParser */
export async function chatStreamApi(
  payload: ChatStreamPayload,
  handlers: ChatStreamHandlers,
) {
  const parser = createSseLineParser(handlers.onEvent);
  await requestClient.postSSE('/chat/stream', payload, {
    headers: {
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
    },
    signal: handlers.signal,
    onMessage: (chunk) => parser.push(chunk),
    onEnd: () => {
      parser.flush();
      handlers.onEnd?.();
    },
  });
}

export type { ChatMessage, Conversation };
