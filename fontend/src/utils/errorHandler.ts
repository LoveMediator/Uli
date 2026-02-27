import { ErrorCode } from '../types/api';

// 错误消息映射
const ERROR_MESSAGES: Record<number, string> = {
  [ErrorCode.PARAM_INVALID]: '参数校验失败',
  [ErrorCode.RESOURCE_NOT_FOUND]: '资源不存在',
  [ErrorCode.STATE_NOT_ALLOWED]: '当前状态不允许该操作',
  [ErrorCode.AUTH_FAILED]: '认证失败，请重新登录',
  [ErrorCode.PERMISSION_DENIED]: '无权限访问该资源',
  [ErrorCode.ACCOUNT_LOCKED]: '账号已被锁定',
  [ErrorCode.RATE_LIMITED]: '请求过于频繁，请稍后再试',
  [ErrorCode.USERNAME_EXISTS]: '用户名已存在',
  [ErrorCode.SNAPSHOT_FROZEN]: '快照已冻结，无法修改',
  [ErrorCode.EVENT_NOT_READY]: '事件尚未满足分析前置条件',
  [ErrorCode.INTERNAL_ERROR]: '系统内部错误，请稍后重试',
};

// 获取错误消息
export const getErrorMessage = (code: number, defaultMessage?: string): string => {
  return ERROR_MESSAGES[code] || defaultMessage || '未知错误';
};

// 判断是否为认证错误
export const isAuthError = (code: number): boolean => {
  return code === ErrorCode.AUTH_FAILED || code === ErrorCode.ACCOUNT_LOCKED;
};

// 判断是否需要重新登录
export const shouldRelogin = (code: number): boolean => {
  return code === ErrorCode.AUTH_FAILED;
};
