import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取用户所有菜单
 * 当前 accessMode=frontend，本地路由生成菜单；后端暂无 /menu/all。
 */
export async function getAllMenusApi() {
  try {
    return await requestClient.get<RouteRecordStringComponent[]>('/menu/all');
  } catch {
    return [];
  }
}
