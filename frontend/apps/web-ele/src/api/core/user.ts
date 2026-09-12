import type { UserInfo } from '@vben/types';

import { preferences } from '@vben/preferences';

import { requestClient } from '#/api/request';

import type { AuthApi } from './auth';

/**
 * 获取用户信息 — 映射 FastAPI /auth/me → Vben UserInfo
 */
export async function getUserInfoApi(): Promise<UserInfo> {
  const me = await requestClient.get<AuthApi.MeResult>('/auth/me');
  return {
    userId: me.id,
    username: me.username,
    realName: me.nickname || me.username,
    avatar: '',
    desc: me.email || '',
    homePath: preferences.app.defaultHomePath,
    token: '',
    roles: me.roles ?? [],
  };
}
