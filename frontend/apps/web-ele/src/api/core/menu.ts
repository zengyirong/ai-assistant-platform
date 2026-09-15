import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '#/api/request';

/** Current user menu tree (Vben backend accessMode). */
export async function getAllMenusApi() {
  // Avoid toast spam on every login; empty on failure → no menus.
  try {
    return await requestClient.get<RouteRecordStringComponent[]>('/menu/all');
  } catch (error) {
    console.error('[menu/all] failed', error);
    return [];
  }
}
