export interface RelayMessageRequest {
  eventId: string;
  targetUserId: string;
  rawMessage: string;
}

export interface RelayMessageResponse {
  messageId: string;
  delivered: boolean;
  finalMessage: string;
}

export interface ElfInboxMessage {
  messageId: string;
  eventId: string | null;
  fromUserId: string;
  fromUsername: string;
  finalMessage: string;
  createdAt: string;
}

export interface ElfInboxData {
  items: ElfInboxMessage[];
}

export interface ModerateMessageRequest {
  rawMessage: string;
}

export interface ModerateMessageResponse {
  blocked: boolean;
  riskLevel: string;
  suggestedMessage: string | null;
}
