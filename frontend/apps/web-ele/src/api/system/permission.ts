import { requestClient } from '#/api/request';

export interface SystemPermission {
  id: string;
  code: string;
  name: string;
  type: string;
  parent_id?: string | null;
  path?: string | null;
  component?: string | null;
  icon?: string | null;
  sort_order: number;
  visible: boolean;
  status: string;
  redirect?: string | null;
  children?: SystemPermission[];
}

export async function listPermissionTreeApi(type?: string) {
  return requestClient.get<{ items: SystemPermission[] }>('/permissions', {
    params: { tree: true, type },
  });
}

export async function listPermissionsApi(type?: string) {
  return requestClient.get<{ items: SystemPermission[] }>('/permissions', {
    params: { type },
  });
}

export async function createPermissionApi(body: Partial<SystemPermission> & {
  code: string;
  name: string;
  type: string;
}) {
  return requestClient.post<SystemPermission>('/permissions', body);
}

export async function updatePermissionApi(
  id: string,
  body: Partial<SystemPermission> & { clear_parent?: boolean },
) {
  return requestClient.put<SystemPermission>(`/permissions/${id}`, body);
}

export async function deletePermissionApi(id: string) {
  return requestClient.delete(`/permissions/${id}`);
}
