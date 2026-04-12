import { apiClient } from '@/shared/api/http/client';

// 创建关系邀请
export const createRelationshipInvite = async () => {
  const response = await apiClient.post('/relationships/invite');
  return response.data;
};

// 接受关系邀请
export const acceptRelationshipInvite = async (inviteCode: string) => {
  const response = await apiClient.post('/relationships/accept', {
    invite_code: inviteCode,
  });
  return response.data;
};

// 获取关系列表
export const getRelationships = async () => {
  const response = await apiClient.get('/relationships');
  return response.data;
};