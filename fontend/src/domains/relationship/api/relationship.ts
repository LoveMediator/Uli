import { unwrapResponse } from '@/shared/api/http';
import { apiClient } from '@/shared/api/http/client';
import type {
  RelationshipAcceptData,
  RelationshipInviteData,
  RelationshipListData,
} from '@/shared/api/types';

// 创建关系邀请
export const createRelationshipInvite = async () => {
  const response = await apiClient.post('/relationships/invite');
  return unwrapResponse<RelationshipInviteData>(response);
};

// 接受关系邀请
export const acceptRelationshipInvite = async (inviteCode: string) => {
  const response = await apiClient.post('/relationships/accept', {
    inviteToken: inviteCode,
  });
  return unwrapResponse<RelationshipAcceptData>(response);
};

// 获取关系列表
export const getRelationships = async () => {
  const response = await apiClient.get('/relationships');
  return unwrapResponse<RelationshipListData>(response);
};
