import type { EventStatusValue } from './enums';

/* ── Analysis Session (新正式流程) ── */

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
  canCommit: boolean;
  factSummary: string | null;
  messages: AnalysisSessionMessagePayload[];
}

export interface AnalysisSessionMessageRequest {
  message: string;
}

export interface AnalysisSessionMessageData {
  sessionId: string;
  reply: string;
  canCommit: boolean;
  factSummary: string | null;
}

export interface AnalysisSessionCommitData {
  sessionId: string;
  eventId: string;
  status: EventStatusValue;
  snapshotAId: string | null;
  snapshotBId: string | null;
  judgeResultId: string | null;
}

/* ── Invite / Snapshot ── */

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

/* ── B-Agree ── */

export interface BAgreeRequest {
  agree: boolean;
}

export interface BAgreeData {
  eventId: string;
  status: EventStatusValue;
  judgeResultId: string;
}

/* ── Judge Result ── */

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

/* ── Followup Chat ── */

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
