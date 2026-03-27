import { apiClient, unwrapResponse } from './client';
import type {
  ModerateMessageRequest,
  ModerateMessageResponse,
  RelayMessageRequest,
  RelayMessageResponse,
} from '@/types';

export async function relayMessage(data: RelayMessageRequest) {
  const response = await apiClient.post('/elf/relay', data);
  return unwrapResponse<RelayMessageResponse>(response);
}

export async function moderateMessage(data: ModerateMessageRequest) {
  const response = await apiClient.post('/elf/moderate', data);
  return unwrapResponse<ModerateMessageResponse>(response);
}
