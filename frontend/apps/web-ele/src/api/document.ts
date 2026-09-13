import type { DocumentItem, DocumentJob, DocumentPage } from '#/types/document';

import { requestClient } from '#/api/request';

export async function listDocumentsApi(
  kbId: string,
  params?: { page?: number; page_size?: number },
) {
  return requestClient.get<DocumentPage>(
    `/knowledge-bases/${kbId}/documents`,
    { params },
  );
}

export async function getDocumentApi(id: string) {
  return requestClient.get<DocumentItem>(`/documents/${id}`);
}

export async function uploadDocumentApi(kbId: string, file: File) {
  return requestClient.upload<DocumentItem>(
    `/knowledge-bases/${kbId}/documents`,
    { file },
  );
}

export async function deleteDocumentApi(id: string) {
  return requestClient.delete(`/documents/${id}`);
}

export async function retryDocumentApi(id: string) {
  return requestClient.post<DocumentJob>(`/documents/${id}/retry`);
}

export async function listDocumentJobsApi(id: string) {
  return requestClient.get<{ items: DocumentJob[] }>(`/documents/${id}/jobs`);
}
