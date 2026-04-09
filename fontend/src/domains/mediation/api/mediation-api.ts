import { apiClient, unwrapResponse } from '@/shared/api/http';
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
  RelayMessageRequest,
  RelayMessageResponse,
  SnapshotAData,
} from '@/shared/api/types';

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

export async function relayMessage(data: RelayMessageRequest) {
  const response = await apiClient.post('/elf/relay', data);
  return unwrapResponse<RelayMessageResponse>(response);
}

export const mediationApi = {
  createEvent,
  commitA,
  getInvite,
  getSnapshotA,
  bAgree,
  commitB,
  getJudgeResult,
  sendFollowupMessage,
  relayMessage,
};
