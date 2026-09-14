import type { OrgUser, OrgUserPage } from '#/types/user';

import { requestClient } from '#/api/request';

export async function listOrgUsersApi(params?: {
  q?: string;
  page?: number;
  page_size?: number;
}) {
  return requestClient.get<OrgUserPage>('/users', { params });
}

export type { OrgUser };
