export interface AuthSession {
  accessToken: string | null;
  refreshToken: string | null;
  tokenType: string | null;
  userId: number | null;
  publicId: string | null;
  usernameDraft: string;
  isAuthenticated: boolean;
}
