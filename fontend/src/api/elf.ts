import apiClient from './client';
import { ApiResponse } from '../types/api';
import {
  RelayMessageRequest,
  RelayMessageResponse,
  ModerateMessageRequest,
  ModerateMessageResponse,
} from '../types/elf';

// 小精灵传话
export const relayMessage = async (data: RelayMessageRequest): Promise<RelayMessageResponse> => {
  const response = await apiClient.post<ApiResponse<RelayMessageResponse>>(
    '/elf/relay',
    data
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 过激语言检测
export const moderateMessage = async (
  data: ModerateMessageRequest
): Promise<ModerateMessageResponse> => {
  const response = await apiClient.post<ApiResponse<ModerateMessageResponse>>(
    '/elf/moderate',
    data
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};
