import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '#/api/request';

/** Current user menu tree (Vben backend accessMode). */
export async function getAllMenusApi() {
  return requestClient.get<RouteRecordStringComponent[]>('/menu/all');
}
