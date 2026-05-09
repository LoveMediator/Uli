import { apiClient, unwrapResponse } from '@/shared/api/http';
import type { ElfInboxData, ModerateMessageRequest, ModerateMessageResponse } from '@/shared/api/types';

export async function moderateMessage(data: ModerateMessageRequest) {
  const response = await apiClient.post('/elf/moderate', data);
  return unwrapResponse<ModerateMessageResponse>(response);
}

export async function getElfMessages(limit = 5) {
  const response = await apiClient.get('/elf/messages', {
    params: { limit },
  });
  return unwrapResponse<ElfInboxData>(response);
}

export const homeApi = {
  getElfMessages,
  moderateMessage,
};
