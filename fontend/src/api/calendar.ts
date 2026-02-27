import apiClient from './client';
import { ApiResponse } from '../types/api';
import { Review, CalendarMonth, UpdateReviewRequest } from '../types/calendar';

// 获取日历数据
export const getCalendar = async (year: number, month: number): Promise<CalendarMonth> => {
  const response = await apiClient.get<ApiResponse<CalendarMonth>>('/calendar', {
    params: { year, month },
  });
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取指定日期的复盘列表
export const getReviewsByDate = async (date: string): Promise<Review[]> => {
  const response = await apiClient.get<ApiResponse<Review[]>>(
    `/calendar/days/${date}/reviews`
  );
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 获取复盘详情
export const getReview = async (reviewId: string): Promise<Review> => {
  const response = await apiClient.get<ApiResponse<Review>>(`/reviews/${reviewId}`);
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 更新复盘
export const updateReview = async (
  reviewId: string,
  data: UpdateReviewRequest
): Promise<Review> => {
  const response = await apiClient.put<ApiResponse<Review>>(`/reviews/${reviewId}`, data);
  if (response.data.code === 0 && response.data.data) {
    return response.data.data;
  }
  throw new Error(response.data.message);
};

// 删除复盘
export const deleteReview = async (reviewId: string): Promise<void> => {
  const response = await apiClient.delete<ApiResponse<null>>(`/reviews/${reviewId}`);
  if (response.data.code !== 0) {
    throw new Error(response.data.message);
  }
};
