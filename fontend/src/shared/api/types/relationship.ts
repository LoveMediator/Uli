export interface RelationshipInviteData {
  inviteToken: string;
  inviteUrl: string;
  expiresAt: string;
}

export interface RelationshipCurrentEvent {
  eventId: string;
  status: string;
  pendingAction: string;
  title: string | null;
}

export interface RelationshipSummary {
  relationshipId: string;
  partnerUserId: string;
  partnerUsername: string;
  status: string;
  currentEvent: RelationshipCurrentEvent | null;
}

export type RelationshipAcceptData = RelationshipSummary;

export interface RelationshipListData {
  items: RelationshipSummary[];
}
