/** Conversation / message types aligned with backend DTO */

import type { SseCitationItem } from './sse';

export interface Conversation {
  id: string;
  org_id: string;
  user_id: string;
  title: string;
  kb_scope: string[] | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ConversationPage {
  items: Conversation[];
  total: number;
  page: number;
  page_size: number;
}

export type MessageRole = 'USER' | 'ASSISTANT';
export type MessageStatus =
  | 'COMPLETED'
  | 'GENERATING'
  | 'FAILED'
  | 'ABORTED';

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  request_id: string | null;
  citations: (SseCitationItem & { sort_order?: number })[];
  created_at: string | null;
}

export interface MessagePage {
  items: ChatMessage[];
  total: number;
  page: number;
  page_size: number;
}

export interface ChatStreamPayload {
  conversation_id: string;
  question: string;
  kb_ids?: string[] | null;
}
