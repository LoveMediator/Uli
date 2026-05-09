import type { EventStatusValue } from '@/shared/api/types';

export interface CurrentEventSession {
  eventId: string;
  title: string;
  status: EventStatusValue;
  pendingAction?: string;
  relationshipId?: string;
  partnerUserId?: string;
  partnerUsername?: string;
  sessionId?: string;
  snapshotAId?: string;
  judgeResultId?: string;
}
