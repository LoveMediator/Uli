export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

export const ErrorCode = {
  success: 0,
  paramInvalid: 1001,
  resourceNotFound: 1002,
  stateNotAllowed: 1003,
  authFailed: 2001,
  permissionDenied: 2002,
  accountLocked: 2003,
  rateLimited: 2004,
  usernameExists: 3001,
  snapshotFrozen: 3002,
  eventNotReady: 3003,
  internalError: 5000,
} as const;

export type ErrorCodeValue = (typeof ErrorCode)[keyof typeof ErrorCode];

export class ApiClientError extends Error {
  code: number;
  status?: number;

  constructor(message: string, code: number = ErrorCode.internalError, status?: number) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.status = status;
  }
}
