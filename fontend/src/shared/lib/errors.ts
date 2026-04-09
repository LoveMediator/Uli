import { ApiClientError, ErrorCode } from '@/shared/api/types';

const errorMessages: Record<number, string> = {
  [ErrorCode.paramInvalid]: '参数不合法，请检查输入内容。',
  [ErrorCode.resourceNotFound]: '目标资源不存在或已失效。',
  [ErrorCode.stateNotAllowed]: '当前状态下暂时不能执行这个操作。',
  [ErrorCode.authFailed]: '登录状态已失效，请重新登录。',
  [ErrorCode.permissionDenied]: '你没有权限访问这项内容。',
  [ErrorCode.accountLocked]: '账号已被锁定，请稍后再试。',
  [ErrorCode.rateLimited]: '请求过于频繁，请稍后再试。',
  [ErrorCode.usernameExists]: '用户名已经存在，请换一个试试。',
  [ErrorCode.snapshotFrozen]: '快照已经冻结，不能再次修改。',
  [ErrorCode.eventNotReady]: '事件还没到可以分析的阶段。',
  [ErrorCode.internalError]: '服务暂时开小差了，请稍后重试。',
};

export function getErrorMessage(error: unknown, fallback = '操作失败，请稍后重试。') {
  if (error instanceof ApiClientError) {
    return errorMessages[error.code] ?? error.message ?? fallback;
  }

  if (error instanceof Error) {
    return error.message || fallback;
  }

  return fallback;
}
