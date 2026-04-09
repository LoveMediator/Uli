import { apiClient, unwrapResponse } from '@/shared/api/http';
import type { ModerateMessageRequest, ModerateMessageResponse } from '@/shared/api/types';

export async function moderateMessage(data: ModerateMessageRequest) {
  const response = await apiClient.post('/elf/moderate', data);
  return unwrapResponse<ModerateMessageResponse>(response);
}

export const homeApi = {
  moderateMessage,
};
