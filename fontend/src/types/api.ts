// 统一响应结构
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T | null;
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// 通用错误码
export const ErrorCode = {
  SUCCESS: 0,
  PARAM_INVALID: 1001,
  RESOURCE_NOT_FOUND: 1002,
  STATE_NOT_ALLOWED: 1003,
  AUTH_FAILED: 2001,
  PERMISSION_DENIED: 2002,
  ACCOUNT_LOCKED: 2003,
  RATE_LIMITED: 2004,
  USERNAME_EXISTS: 3001,
  SNAPSHOT_FROZEN: 3002,
  EVENT_NOT_READY: 3003,
  INTERNAL_ERROR: 5000,
} as const;

export type ErrorCode = typeof ErrorCode[keyof typeof ErrorCode];
