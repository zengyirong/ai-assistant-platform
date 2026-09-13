import { requestClient } from '#/api/request';

export interface SpaceItem {
  id: string;
  org_id: string;
  name: string;
  description: string | null;
  is_default: number;
  owner_id: string | null;
}

export async function listSpacesApi() {
  return requestClient.get<{ items: SpaceItem[] }>('/spaces');
}
