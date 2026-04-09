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

export interface ModerateMessageRequest {
  rawMessage: string;
}

export interface ModerateMessageResponse {
  blocked: boolean;
  riskLevel: string;
  suggestedMessage: string | null;
}
