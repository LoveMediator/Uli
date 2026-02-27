// 事件状态
export const EventStatus = {
  DRAFT: 'draft',
  WAITING_B: 'waiting_B',
  JUDGED: 'judged',
  REVIEWED: 'reviewed',
  CLOSED: 'closed',
} as const;

export type EventStatus = typeof EventStatus[keyof typeof EventStatus];

// 用户状态
export const UserStatus = {
  ACTIVE: 'active',
  LOCKED: 'locked',
  DISABLED: 'disabled',
} as const;

export type UserStatus = typeof UserStatus[keyof typeof UserStatus];

// 消息角色
export const MessageRole = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
} as const;

export type MessageRole = typeof MessageRole[keyof typeof MessageRole];
