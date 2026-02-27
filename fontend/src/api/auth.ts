import apiClient, { setTokens, clearTokens } from './client';
import { ApiResponse } from '../types/api';
import {
  RegisterRequest,
  LoginRequest,
  RefreshTokenRequest,
  TokenResponse,
  User,
} from '../types/auth';

// 注册
export const register = async (data: RegisterRequest): Promise<TokenResponse> => {
  const response = await apiClient.post<ApiResponse<TokenResponse>>('/auth/register', data);
  if (response.data.code === 0 && response.data.data) {
    const { accessToken, refreshToken } = response.data.data;
    setTokens(accessToken, refreshToken);
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 登录
export const login = async (data: LoginRequest): Promise<TokenResponse> => {
  const response = await apiClient.post<ApiResponse<TokenResponse>>('/auth/login', data);
  if (response.data.code === 0 && response.data.data) {
    const { accessToken, refreshToken } = response.data.data;
    setTokens(accessToken, refreshToken);
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 登出
export const logout = async (): Promise<void> => {
  try {
    await apiClient.post<ApiResponse<null>>('/auth/logout');
  } finally {
    clearTokens();
  }
};

// 刷新Token
export const refreshAccessToken = async (data: RefreshTokenRequest): Promise<TokenResponse> => {
  const response = await apiClient.post<ApiResponse<TokenResponse>>('/auth/refresh', data);
  if (response.data.code === 0 && response.data.data) {
    const { accessToken, refreshToken } = response.data.data;
    setTokens(accessToken, refreshToken);
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取当前用户信息
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<ApiResponse<User>>('/auth/me');
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};
