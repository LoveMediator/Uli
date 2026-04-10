import { apiClient, unwrapResponse } from '@/shared/api/http';
import type {
  AnalysisSessionCommitData,
  AnalysisSessionData,
  AnalysisSessionMessageData,
  AnalysisSessionMessageRequest,
  BAgreeData,
  BAgreeRequest,
  FollowupRequest,
  FollowupResponse,
  InviteData,
  JudgeResultData,
  RelayMessageRequest,
  RelayMessageResponse,
  SnapshotAData,
} from '@/shared/api/types';

/**
 * POST /relationships/{relationshipId}/analysis-sessions/a
 * Starts or resumes A-side private analysis.
 */
export async function startAAnalysisSession(
  relationshipId: string,
) {
  const response = await apiClient.post(`/relationships/${relationshipId}/analysis-sessions/a`);
  return unwrapResponse<AnalysisSessionData>(response);
}

/**
 * POST /events/{eventId}/analysis-sessions/b
 * Starts or resumes B-side private analysis.
 */
export async function startBAnalysisSession(eventId: string) {
  const response = await apiClient.post(`/events/${eventId}/analysis-sessions/b`);
  return unwrapResponse<AnalysisSessionData>(response);
}

/**
 * POST /analysis-sessions/{sessionId}/messages
 * Sends one text message into a private analysis session.
 */
export async function sendAnalysisMessage(sessionId: string, data: AnalysisSessionMessageRequest) {
  const response = await apiClient.post(`/analysis-sessions/${sessionId}/messages`, data);
  return unwrapResponse<AnalysisSessionMessageData>(response);
}

/**
 * POST /analysis-sessions/{sessionId}/commit
 * Commits the current private analysis session into business state.
 */
export async function commitAnalysisSession(sessionId: string) {
  const response = await apiClient.post(`/analysis-sessions/${sessionId}/commit`);
  return unwrapResponse<AnalysisSessionCommitData>(response);
}

/**
 * GET /events/{eventId}/invite
 * Reads the public invite information for one event.
 */
export async function getInvite(eventId: string) {
  const response = await apiClient.get(`/events/${eventId}/invite`);
  return unwrapResponse<InviteData>(response);
}

/**
 * GET /events/{eventId}/snapshot-a
 * Reads A-side frozen snapshot after authentication.
 */
export async function getSnapshotA(eventId: string) {
  const response = await apiClient.get(`/events/${eventId}/snapshot-a`);
  return unwrapResponse<SnapshotAData>(response);
}

/**
 * POST /events/{eventId}/b-agree
 * Lets B directly agree with Snapshot_A and trigger judge generation.
 */
export async function bAgree(eventId: string, data: BAgreeRequest) {
  const response = await apiClient.post(`/events/${eventId}/b-agree`, data);
  return unwrapResponse<BAgreeData>(response);
}

/**
 * GET /events/{eventId}/judge-result
 * Reads the generated judge result for one event.
 */
export async function getJudgeResult(eventId: string) {
  const response = await apiClient.get(`/events/${eventId}/judge-result`);
  return unwrapResponse<JudgeResultData>(response);
}

/**
 * POST /events/{eventId}/followup-chat/messages
 * Sends one follow-up question after the judge result exists.
 */
export async function sendFollowupMessage(eventId: string, data: FollowupRequest) {
  const response = await apiClient.post(`/events/${eventId}/followup-chat/messages`, data);
  return unwrapResponse<FollowupResponse>(response);
}

/**
 * POST /elf/relay
 * Lets the assistant rewrite and relay a message to the target user.
 */
export async function relayMessage(data: RelayMessageRequest) {
  const response = await apiClient.post('/elf/relay', data);
  return unwrapResponse<RelayMessageResponse>(response);
}

export const mediationApi = {
  startAAnalysisSession,
  startBAnalysisSession,
  sendAnalysisMessage,
  commitAnalysisSession,
  getInvite,
  getSnapshotA,
  bAgree,
  getJudgeResult,
  sendFollowupMessage,
  relayMessage,
};
