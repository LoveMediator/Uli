import type { EventStatusValue } from './enums';

export interface CreateEventRequest {
  title: string;
  relationshipId: string;
}

export interface CreateEventData {
  eventId: string;
  status: EventStatusValue;
}

export interface CommitARequest {
  confirmText: string;
}

export interface CommitAData {
  eventId: string;
  status: EventStatusValue;
  snapshotAId: string;
}

export interface StartAnalysisSessionARequest {
  eventId?: string;
  title?: string;
}

export interface AnalysisSessionImagePayload {
  imageId: string;
  mimeType: string;
  filename: string | null;
}

export interface AnalysisSessionMessagePayload {
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  images: AnalysisSessionImagePayload[];
}

export interface AnalysisSessionData {
  sessionId: string;
  phase: 'a' | 'b';
  relationshipId: string | null;
  eventId: string | null;
  expiresAt: string;
  messages: AnalysisSessionMessagePayload[];
}

export interface AnalysisSessionMessageRequest {
  message: string;
}

export interface AnalysisSessionMessageData {
  sessionId: string;
  reply: string;
}

export interface AnalysisSessionCommitData {
  sessionId: string;
  eventId: string;
  status: EventStatusValue;
  snapshotAId: string | null;
  snapshotBId: string | null;
  judgeResultId: string | null;
}

export interface InviteData {
  eventId: string;
  status: EventStatusValue;
  title: string | null;
  inviteMessage: string;
  requiresAuth: boolean;
}

export interface SnapshotPayload {
  summary: string;
  pointsA: string[];
  pointsB: string[];
}

export interface SnapshotAData {
  eventId: string;
  status: EventStatusValue;
  snapshotA: SnapshotPayload;
}

export interface BAgreeRequest {
  agree: boolean;
}

export interface BAgreeData {
  eventId: string;
  status: EventStatusValue;
  judgeResultId: string;
}

export interface CommitBRequest {
  summary: string;
  pointsA: string[];
  pointsB: string[];
}

export interface CommitBData {
  eventId: string;
  status: EventStatusValue;
  snapshotBId: string;
  judgeResultId: string;
}

export interface JudgeAnalysis {
  triggers: string[];
  misunderstandings: string[];
  adviceForA: string[];
  adviceForB: string[];
}

export interface JudgeResultData {
  judgeResultId: string;
  eventId: string;
  status: EventStatusValue;
  objectiveSummary: string;
  analysis: JudgeAnalysis;
  createdAt: string;
}

export interface FollowupRequest {
  message: string;
}

export interface FollowupContextMeta {
  recentMessages: number;
  snapshots: number;
  judgeResults: number;
}

export interface FollowupResponse {
  reply: string;
  contextMeta: FollowupContextMeta;
}
