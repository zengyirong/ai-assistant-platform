import { requestClient } from '#/api/request';

export interface SystemRole {
  id: string;
  org_id: string;
  code: string;
  name: string;
  status: string;
  permission_ids?: string[];
  permission_codes?: string[];
}

export async function listRolesApi(params?: {
  page?: number;
  page_size?: number;
}) {
  return requestClient.get<{
    items: SystemRole[];
    total: number;
  }>('/roles', { params });
}

export async function createRoleApi(body: {
  code: string;
  name: string;
  status?: string;
}) {
  return requestClient.post<SystemRole>('/roles', body);
}

export async function updateRoleApi(
  roleId: string,
  body: { name?: string; status?: string },
) {
  return requestClient.put<SystemRole>(`/roles/${roleId}`, body);
}

export async function setRolePermissionsApi(
  roleId: string,
  permission_ids: string[],
) {
  return requestClient.put<SystemRole>(`/roles/${roleId}/permissions`, {
    permission_ids,
  });
}
