import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '@/lib/constants';
import { useAuthStore } from '@/stores/auth-store';
import { ApiClientError, type ApiResponse, ErrorCode } from '@/types/api';
import type { RefreshTokenResponse } from '@/types/auth';

type RetriableRequest = InternalAxiosRequestConfig & { _retry?: boolean };

const authFreePaths = ['/auth/login', '/auth/register', '/auth/refresh'];

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
  },
});

apiClient.interceptors.request.use((config) => {
  const accessToken = useAuthStore.getState().accessToken;

  if (accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const originalRequest = error.config as RetriableRequest | undefined;
    const requestUrl = originalRequest?.url ?? '';
    const isAuthFreeRequest = authFreePaths.some((path) => requestUrl.includes(path));

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthFreeRequest) {
      originalRequest._retry = true;

      const refreshToken = useAuthStore.getState().refreshToken;
      if (!refreshToken) {
        useAuthStore.getState().clearSession();
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

        useAuthStore
          .getState()
          .updateAccessToken(
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
        if (window.location.pathname.startsWith('/app')) {
          window.location.assign('/login');
        }
      }
    }

    const status = error.response?.status;
    const message = error.response?.data?.message ?? error.message ?? '请求失败';
    const code = error.response?.data?.code ?? ErrorCode.internalError;
    return Promise.reject(new ApiClientError(message, code, status));
  },
);

export function unwrapResponse<T>(response: { data: ApiResponse<T>; status?: number }) {
  if (response.data.code !== ErrorCode.success || response.data.data === null) {
    throw new ApiClientError(response.data.message, response.data.code, response.status);
  }

  return response.data.data;
}
