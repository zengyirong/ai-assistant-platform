/** Knowledge base types aligned with backend DTO */

export type KbVisibility = 'PRIVATE' | 'SPACE';
export type KbStatus = 'ACTIVE' | 'ARCHIVED';
export type KbMemberRole = 'OWNER' | 'EDITOR' | 'VIEWER';

export interface KnowledgeBase {
  id: string;
  org_id: string;
  space_id: string | null;
  name: string;
  description: string | null;
  visibility: KbVisibility;
  status: KbStatus;
  created_by: string;
  document_count?: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface KnowledgeBasePage {
  items: KnowledgeBase[];
  total: number;
  page: number;
  page_size: number;
}

export interface KnowledgeBaseCreatePayload {
  name: string;
  description?: string | null;
  visibility: KbVisibility;
  space_id?: string | null;
}

export interface KnowledgeBaseUpdatePayload {
  name?: string;
  description?: string | null;
  visibility?: KbVisibility;
  space_id?: string | null;
}

export interface KbMember {
  user_id: string;
  role: KbMemberRole;
  created_at: string | null;
}

export interface RagConfig {
  id: string;
  kb_id: string;
  chunk_strategy: string;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  score_threshold: number | null;
  llm_model: string | null;
  temperature: number;
  system_prompt: string | null;
  created_at: string | null;
  updated_at: string | null;
}
