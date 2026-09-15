import { requestClient } from '#/api/request';

export interface SpaceItem {
  id: string;
  org_id: string;
  name: string;
  description: string | null;
  is_default: boolean | number;
  owner_id: string | null;
}

export interface SpaceMember {
  id: string;
  space_id: string;
  user_id: string;
  role: string;
  username?: string;
  nickname?: string | null;
}

export async function listSpacesApi() {
  return requestClient.get<{ items: SpaceItem[] }>('/spaces');
}

export async function createSpaceApi(body: {
  name: string;
  description?: string;
}) {
  return requestClient.post<SpaceItem>('/spaces', body);
}

export async function updateSpaceApi(
  spaceId: string,
  body: { name?: string; description?: string },
) {
  return requestClient.put<SpaceItem>(`/spaces/${spaceId}`, body);
}

export async function listSpaceMembersApi(spaceId: string) {
  return requestClient.get<{ items: SpaceMember[] }>(
    `/spaces/${spaceId}/members`,
  );
}

export async function upsertSpaceMemberApi(
  spaceId: string,
  body: { user_id: string; role?: string },
) {
  return requestClient.post<SpaceMember>(`/spaces/${spaceId}/members`, body);
}

export async function removeSpaceMemberApi(spaceId: string, userId: string) {
  return requestClient.delete(`/spaces/${spaceId}/members/${userId}`);
}
