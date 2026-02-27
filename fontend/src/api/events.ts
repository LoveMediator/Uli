import apiClient from './client';
import { ApiResponse } from '../types/api';
import {
  Event,
  Snapshot,
  ChatMessage,
  JudgeResult,
  CreateEventRequest,
  SendPrivateChatRequest,
  CommitSnapshotARequest,
  BAgreementRequest,
  CommitSnapshotBRequest,
  SendFollowupChatRequest,
} from '../types/event';

// 创建事件
export const createEvent = async (data: CreateEventRequest): Promise<Event> => {
  const response = await apiClient.post<ApiResponse<Event>>('/events', data);
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取事件详情
export const getEvent = async (eventId: string): Promise<Event> => {
  const response = await apiClient.get<ApiResponse<Event>>(`/events/${eventId}`);
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取事件列表
export const getEvents = async (): Promise<Event[]> => {
  const response = await apiClient.get<ApiResponse<Event[]>>('/events');
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 发送私聊消息（A方分析阶段）
export const sendPrivateChat = async (
  eventId: string,
  data: SendPrivateChatRequest
): Promise<ChatMessage[]> => {
  const response = await apiClient.post<ApiResponse<ChatMessage[]>>(
    `/events/${eventId}/private-chat/messages`,
    data
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取私聊历史
export const getPrivateChatHistory = async (eventId: string): Promise<ChatMessage[]> => {
  const response = await apiClient.get<ApiResponse<ChatMessage[]>>(
    `/events/${eventId}/private-chat/messages`
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 提交快照A（冻结）
export const commitSnapshotA = async (
  eventId: string,
  data: CommitSnapshotARequest
): Promise<Snapshot> => {
  const response = await apiClient.post<ApiResponse<Snapshot>>(
    `/events/${eventId}/commit-a`,
    data
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// B方同意/不同意
export const submitBAgreement = async (
  eventId: string,
  data: BAgreementRequest
): Promise<void> => {
  const response = await apiClient.post<ApiResponse<null>>(
    `/events/${eventId}/b-agree`,
    data
  );
  if (response.data.code !== 0) {
    throw new Error(response.data.message);
  }
};

// 提交快照B
export const commitSnapshotB = async (
  eventId: string,
  data: CommitSnapshotBRequest
): Promise<Snapshot> => {
  const response = await apiClient.post<ApiResponse<Snapshot>>(
    `/events/${eventId}/commit-b`,
    data
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取裁判结果
export const getJudgeResult = async (eventId: string): Promise<JudgeResult> => {
  const response = await apiClient.get<ApiResponse<JudgeResult>>(
    `/events/${eventId}/judge-result`
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 发送复盘消息
export const sendFollowupChat = async (
  eventId: string,
  data: SendFollowupChatRequest
): Promise<ChatMessage[]> => {
  const response = await apiClient.post<ApiResponse<ChatMessage[]>>(
    `/events/${eventId}/followup-chat/messages`,
    data
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取复盘聊天历史
export const getFollowupChatHistory = async (eventId: string): Promise<ChatMessage[]> => {
  const response = await apiClient.get<ApiResponse<ChatMessage[]>>(
    `/events/${eventId}/followup-chat/messages`
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取快照A
export const getSnapshotA = async (eventId: string): Promise<Snapshot> => {
  const response = await apiClient.get<ApiResponse<Snapshot>>(
    `/events/${eventId}/snapshot-a`
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取快照B
export const getSnapshotB = async (eventId: string): Promise<Snapshot> => {
  const response = await apiClient.get<ApiResponse<Snapshot>>(
    `/events/${eventId}/snapshot-b`
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};
