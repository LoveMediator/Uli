// 小精灵传话请求
export interface RelayMessageRequest {
  targetUserId: string;
  originalMessage: string;
}

// 小精灵传话响应
export interface RelayMessageResponse {
  relayedMessage: string;
  tone: string;
}

// 过激语言检测请求
export interface ModerateMessageRequest {
  message: string;
}

// 过激语言检测响应
export interface ModerateMessageResponse {
  blocked: boolean;
  riskLevel: 'low' | 'medium' | 'high';
  suggestedMessage?: string;
}
