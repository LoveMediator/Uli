import type { EventStatusValue } from '@/shared/api/types';

export interface CurrentEventSession {
  eventId: string;
  title: string;
  status: EventStatusValue;
  snapshotAId?: string;
  judgeResultId?: string;
}
