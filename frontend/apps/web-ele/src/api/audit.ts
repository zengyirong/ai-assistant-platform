import type { AuditLogPage } from '#/types/audit';

import { requestClient } from '#/api/request';

export async function listAuditLogsApi(params?: {
  page?: number;
  page_size?: number;
  action?: string;
  user_id?: string;
}) {
  return requestClient.get<AuditLogPage>('/audit-logs', { params });
}
