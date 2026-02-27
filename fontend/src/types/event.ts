import { EventStatus, MessageRole } from './enums';

// 事件
export interface Event {
  id: string;
  relationshipId: string;
  status: EventStatus;
  createdAt: string;
  updatedAt: string;
  snapshotAId?: string;
  snapshotBId?: string;
  judgeResultId?: string;
  reviewId?: string;
}

// 快照
export interface Snapshot {
  id: string;
  eventId: string;
  userId: string;
  title: string;
  description: string;
  context: string;
  frozenAt?: string;
  createdAt: string;
}

// 聊天消息
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
}

// 裁判结果
export interface JudgeResult {
  id: string;
  eventId: string;
  summary: string;
  aResponsibility: number;
  bResponsibility: number;
  suggestions: string[];
  generatedAt: string;
}

// 创建事件请求
export interface CreateEventRequest {
  title: string;
  initialMessage: string;
}

// 发送私聊消息请求
export interface SendPrivateChatRequest {
  message: string;
}

// 提交快照A请求
export interface CommitSnapshotARequest {
  title: string;
  description: string;
}

// B方同意请求
export interface BAgreementRequest {
  agree: boolean;
  reason?: string;
}

// 提交快照B请求
export interface CommitSnapshotBRequest {
  title: string;
  description: string;
}

// 发送复盘消息请求
export interface SendFollowupChatRequest {
  message: string;
}
