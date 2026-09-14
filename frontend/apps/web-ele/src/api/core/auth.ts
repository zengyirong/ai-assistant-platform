import { useAccessStore } from '@vben/stores';

import { baseRequestClient, requestClient } from '#/api/request';

export namespace AuthApi {
  /** 登录接口参数 */
  export interface LoginParams {
    password?: string;
    username?: string;
  }

  /** 登录接口返回值（对齐 FastAPI） */
  export interface LoginResult {
    accessToken: string;
    access_token?: string;
    expires_in?: number;
    token_type?: string;
    user?: {
      id: string;
      nickname?: string | null;
      org_id?: string;
      roles?: string[];
      username: string;
    };
  }

  /** /auth/me 原始响应 */
  export interface MeResult {
    email?: string | null;
    id: string;
    nickname?: string | null;
    org_id: string;
    permissions: string[];
    roles: string[];
    username: string;
  }

  export interface RefreshTokenResult {
    data: string;
    status: number;
  }
}

/**
 * 登录 — 归一化为前端使用的 accessToken
 */
export async function loginApi(data: AuthApi.LoginParams) {
  const result = await requestClient.post<AuthApi.LoginResult>(
    '/auth/login',
    data,
  );
  return {
    ...result,
    accessToken: result.accessToken || result.access_token || '',
  };
}

/**
 * 刷新accessToken（一期后端无 refresh，保留占位）
 */
export async function refreshTokenApi() {
  return baseRequestClient.post<AuthApi.RefreshTokenResult>(
    '/auth/refresh',
    undefined,
    {
      withCredentials: true,
    },
  );
}

/**
 * 退出登录（走 baseRequestClient，避免鉴权拦截器对 401 再触发 logout）
 */
export async function logoutApi() {
  const accessStore = useAccessStore();
  const token = accessStore.accessToken;
  return baseRequestClient.post(
    '/auth/logout',
    {},
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  );
}

/**
 * 获取用户权限码（来自 /auth/me.permissions）
 */
export async function getAccessCodesApi() {
  const me = await requestClient.get<AuthApi.MeResult>('/auth/me');
  return me.permissions ?? [];
}
