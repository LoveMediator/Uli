import { apiClient, unwrapResponse } from './client';
import type {
  BAgreeData,
  BAgreeRequest,
  CommitAData,
  CommitARequest,
  CommitBData,
  CommitBRequest,
  CreateEventData,
  CreateEventRequest,
  FollowupRequest,
  FollowupResponse,
  InviteData,
  JudgeResultData,
  SnapshotAData,
} from '@/types';

export async function createEvent(data: CreateEventRequest) {
  const response = await apiClient.post('/events', data);
  return unwrapResponse<CreateEventData>(response);
}

export async function commitA(eventId: string, data: CommitARequest) {
  const response = await apiClient.post(`/events/${eventId}/commit-a`, data);
  return unwrapResponse<CommitAData>(response);
}

export async function getInvite(eventId: string) {
  const response = await apiClient.get(`/events/${eventId}/invite`);
  return unwrapResponse<InviteData>(response);
}

export async function getSnapshotA(eventId: string) {
  const response = await apiClient.get(`/events/${eventId}/snapshot-a`);
  return unwrapResponse<SnapshotAData>(response);
}

export async function bAgree(eventId: string, data: BAgreeRequest) {
  const response = await apiClient.post(`/events/${eventId}/b-agree`, data);
  return unwrapResponse<BAgreeData>(response);
}

export async function commitB(eventId: string, data: CommitBRequest) {
  const response = await apiClient.post(`/events/${eventId}/commit-b`, data);
  return unwrapResponse<CommitBData>(response);
}

export async function getJudgeResult(eventId: string) {
  const response = await apiClient.get(`/events/${eventId}/judge-result`);
  return unwrapResponse<JudgeResultData>(response);
}

export async function sendFollowupMessage(eventId: string, data: FollowupRequest) {
  const response = await apiClient.post(`/events/${eventId}/followup-chat/messages`, data);
  return unwrapResponse<FollowupResponse>(response);
}
