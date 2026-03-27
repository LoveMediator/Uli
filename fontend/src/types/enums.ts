export const EventStatus = {
  draft: 'draft',
  waitingB: 'waiting_b',
  judged: 'judged',
  reviewed: 'reviewed',
  closed: 'closed',
} as const;

export type EventStatusValue = (typeof EventStatus)[keyof typeof EventStatus];
