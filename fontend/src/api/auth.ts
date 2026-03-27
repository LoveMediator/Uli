import { apiClient, unwrapResponse } from './client';
import type {
  AuthTokensData,
  LoginRequest,
  LogoutRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  RegisterRequest,
  RegisterResponseData,
} from '@/types';

export async function register(data: RegisterRequest) {
  const response = await apiClient.post('/auth/register', data);
  return unwrapResponse<RegisterResponseData>(response);
}

export async function login(data: LoginRequest) {
  const response = await apiClient.post('/auth/login', data);
  return unwrapResponse<AuthTokensData>(response);
}

export async function refreshAccessToken(data: RefreshTokenRequest) {
  const response = await apiClient.post('/auth/refresh', data);
  return unwrapResponse<RefreshTokenResponse>(response);
}

export async function logout(data: LogoutRequest) {
  const response = await apiClient.post('/auth/logout', data);
  return unwrapResponse<{ revoked: boolean }>(response);
}
