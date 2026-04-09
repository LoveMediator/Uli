import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/domains/auth/model/auth-store';
import { beginTrackedRequest, endTrackedRequest } from '@/shared/api/http/request-state';
import { API_BASE_URL, API_TIMEOUT_MS } from '@/shared/config/env';
import type { RefreshTokenResponse } from '@/shared/api/types';
import { ApiClientError, ErrorCode, type ApiResponse } from '@/shared/api/types/api';
import { pushMessage } from '@/shared/ui/message-store';

type RetriableRequest = InternalAxiosRequestConfig & {
  _retry?: boolean;
  _silent?: boolean;
};

const authFreePaths = ['/auth/login', '/auth/register', '/auth/refresh'];

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
  },
});

apiClient.interceptors.request.use((config) => {
  const trackedConfig = config as RetriableRequest;

  if (!trackedConfig._silent) {
    beginTrackedRequest();
  }

  const traceId = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;
  config.headers.set?.('X-Trace-Id', traceId);

  const accessToken = useAuthStore.getState().accessToken;
  if (accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    if (!(response.config as RetriableRequest)._silent) {
      endTrackedRequest();
    }

    return response;
  },
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const originalRequest = error.config as RetriableRequest | undefined;
    if (originalRequest && !originalRequest._silent) {
      endTrackedRequest();
    }

    const requestUrl = originalRequest?.url ?? '';
    const isAuthFreeRequest = authFreePaths.some((path) => requestUrl.includes(path));

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthFreeRequest) {
      originalRequest._retry = true;

      const refreshToken = useAuthStore.getState().refreshToken;
      if (!refreshToken) {
        useAuthStore.getState().clearSession();
        pushMessage({
          tone: 'warning',
          text: '登录状态已失效，请重新登录。',
        });
        return Promise.reject(new ApiClientError('登录状态已失效，请重新登录。', ErrorCode.authFailed, 401));
      }

      try {
        const response = await axios.post<ApiResponse<RefreshTokenResponse>>(
          `${API_BASE_URL}/auth/refresh`,
          { refreshToken },
          {
            headers: {
              'Content-Type': 'application/json; charset=utf-8',
            },
          },
        );

        if (response.data.code !== ErrorCode.success || !response.data.data) {
          throw new ApiClientError(response.data.message, response.data.code, response.status);
        }

        useAuthStore.getState().updateAccessToken(
          response.data.data.accessToken,
          response.data.data.tokenType,
          response.data.data.userId,
        );

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${response.data.data.accessToken}`;
        }

        return apiClient(originalRequest);
      } catch {
        useAuthStore.getState().clearSession();
        pushMessage({
          tone: 'warning',
          text: '登录状态已过期，请重新登录后继续。',
        });
        if (window.location.pathname.startsWith('/app')) {
          window.location.assign('/login');
        }

        return Promise.reject(new ApiClientError('登录状态已过期，请重新登录。', ErrorCode.authFailed, 401));
      }
    }

    const status = error.response?.status;
    const message = resolveHttpErrorMessage(error);
    const code = error.response?.data?.code ?? ErrorCode.internalError;

    maybeNotifyGlobalError(status, code, message, requestUrl);
    return Promise.reject(new ApiClientError(message, code, status));
  },
);

export function unwrapResponse<T>(response: { data: ApiResponse<T>; status?: number }) {
  if (response.data.code !== ErrorCode.success || response.data.data === null) {
    throw new ApiClientError(response.data.message, response.data.code, response.status);
  }

  return response.data.data;
}

function resolveHttpErrorMessage(error: AxiosError<ApiResponse<unknown>>) {
  if (error.code === 'ECONNABORTED') {
    return '请求超时，请稍后重试。';
  }

  if (!error.response) {
    return '网络连接异常，请检查后端服务或本地代理。';
  }

  if (error.response.data?.message) {
    return error.response.data.message;
  }

  if (error.response.status === 403) {
    return '当前账号没有权限执行这个操作。';
  }

  if (error.response.status === 404) {
    return '请求的接口或资源不存在。';
  }

  if (error.response.status >= 500) {
    return '服务暂时不可用，请稍后重试。';
  }

  return error.message || '请求失败。';
}

function maybeNotifyGlobalError(
  status: number | undefined,
  code: number,
  message: string,
  requestUrl: string,
) {
  const isAuthRoute = authFreePaths.some((path) => requestUrl.includes(path));

  if (status === 401 && !isAuthRoute) {
    return;
  }

  if (!status || status >= 500) {
    pushMessage({
      tone: 'error',
      text: message,
    });
    return;
  }

  if (status === 403 || status === 404) {
    pushMessage({
      tone: 'warning',
      text: message,
    });
    return;
  }

  if (code === ErrorCode.internalError) {
    pushMessage({
      tone: 'error',
      text: message,
    });
  }
}
