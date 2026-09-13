import type {
  KnowledgeBase,
  KnowledgeBaseCreatePayload,
  KnowledgeBasePage,
  KnowledgeBaseUpdatePayload,
  KbMember,
  KbMemberRole,
  RagConfig,
} from '#/types/knowledge';

import { requestClient } from '#/api/request';

export async function listKnowledgeBasesApi(params?: {
  page?: number;
  page_size?: number;
}) {
  return requestClient.get<KnowledgeBasePage>('/knowledge-bases', { params });
}

export async function getKnowledgeBaseApi(id: string) {
  return requestClient.get<KnowledgeBase>(`/knowledge-bases/${id}`);
}

export async function createKnowledgeBaseApi(data: KnowledgeBaseCreatePayload) {
  return requestClient.post<KnowledgeBase>('/knowledge-bases', data);
}

export async function updateKnowledgeBaseApi(
  id: string,
  data: KnowledgeBaseUpdatePayload,
) {
  return requestClient.put<KnowledgeBase>(`/knowledge-bases/${id}`, data);
}

export async function deleteKnowledgeBaseApi(id: string) {
  return requestClient.delete(`/knowledge-bases/${id}`);
}

export async function listKbMembersApi(id: string) {
  return requestClient.get<{ items: KbMember[] }>(
    `/knowledge-bases/${id}/members`,
  );
}

export async function addKbMemberApi(
  id: string,
  data: { user_id: string; role: KbMemberRole },
) {
  return requestClient.post(`/knowledge-bases/${id}/members`, data);
}

export async function removeKbMemberApi(id: string, userId: string) {
  return requestClient.delete(`/knowledge-bases/${id}/members/${userId}`);
}

export async function getRagConfigApi(id: string) {
  return requestClient.get<RagConfig>(`/knowledge-bases/${id}/rag-config`);
}

export async function updateRagConfigApi(
  id: string,
  data: Partial<RagConfig>,
) {
  return requestClient.put<RagConfig>(
    `/knowledge-bases/${id}/rag-config`,
    data,
  );
}
