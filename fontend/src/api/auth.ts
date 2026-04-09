import {
  authApi as domainAuthApi,
  login,
  logout,
  refreshAccessToken,
  register,
} from '@/domains/auth';

export { login, logout, refreshAccessToken, register };

export const authApi = domainAuthApi;
