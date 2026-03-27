export interface RegisterRequest {
  username: string;
  password: string;
}

export interface RegisterResponseData {
  userId: number;
  publicId: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthTokensData {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  userId: number;
  publicId: string;
}

export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface RefreshTokenResponse {
  accessToken: string;
  tokenType: string;
  userId: number;
}

export interface LogoutRequest {
  refreshToken: string;
}

export interface AuthSession {
  accessToken: string | null;
  refreshToken: string | null;
  tokenType: string | null;
  userId: number | null;
  publicId: string | null;
  usernameDraft: string;
  isAuthenticated: boolean;
}
