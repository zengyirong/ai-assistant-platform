import { requestClient } from '#/api/request';

export interface SystemUser {
  id: string;
  username: string;
  nickname?: string | null;
  email?: string | null;
  status: string;
  org_id?: string;
  roles?: string[];
  role_ids?: string[];
  created_at?: string | null;
}

export async function listSystemUsersApi(params?: {
  q?: string;
  page?: number;
  page_size?: number;
  include_disabled?: boolean;
}) {
  return requestClient.get<{
    items: SystemUser[];
    total: number;
    page: number;
    page_size: number;
  }>('/users', {
    params: { include_disabled: true, ...params },
  });
}

export async function createSystemUserApi(body: {
  username: string;
  password: string;
  nickname?: string;
  email?: string;
  role_ids?: string[];
}) {
  return requestClient.post<SystemUser>('/users', body);
}

export async function updateSystemUserApi(
  userId: string,
  body: { nickname?: string; email?: string; status?: string },
) {
  return requestClient.put<SystemUser>(`/users/${userId}`, body);
}

export async function resetSystemUserPasswordApi(
  userId: string,
  password: string,
) {
  return requestClient.post(`/users/${userId}/reset-password`, { password });
}

export async function setSystemUserRolesApi(
  userId: string,
  role_ids: string[],
) {
  return requestClient.put<SystemUser>(`/users/${userId}/roles`, { role_ids });
}
