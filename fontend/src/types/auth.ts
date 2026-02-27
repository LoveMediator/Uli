import { UserStatus } from './enums';

// 用户信息
export interface User {
  id: string;
  username: string;
  status: UserStatus;
  createdAt: string;
  relationshipId?: string;
}

// Token响应
export interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  user: User;
}

// 注册请求
export interface RegisterRequest {
  username: string;
  password: string;
  confirmPassword: string;
}

// 登录请求
export interface LoginRequest {
  username: string;
  password: string;
}

// 刷新Token请求
export interface RefreshTokenRequest {
  refreshToken: string;
}
