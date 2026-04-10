import type { EventStatusValue } from '@/shared/api/types';

export interface CurrentEventSession {
  eventId: string;
  title: string;
  status: EventStatusValue;
  sessionId?: string;
  snapshotAId?: string;
  judgeResultId?: string;
}
