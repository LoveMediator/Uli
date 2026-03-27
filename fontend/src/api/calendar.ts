import { apiClient, unwrapResponse } from './client';
import type {
  CalendarMonthData,
  ReviewDetail,
  ReviewListItem,
  ReviewUpdateResponse,
  UpdateReviewRequest,
} from '@/types';

export async function getCalendar(month: string, relationshipId: string) {
  const response = await apiClient.get('/calendar', {
    params: {
      month,
      relationshipId,
    },
  });

  return unwrapResponse<CalendarMonthData>(response);
}

export async function getReviewsByDate(date: string, relationshipId: string) {
  const response = await apiClient.get(`/calendar/days/${date}/reviews`, {
    params: {
      relationshipId,
    },
  });

  return unwrapResponse<{ date: string; items: ReviewListItem[] }>(response);
}

export async function getReview(reviewId: string) {
  const response = await apiClient.get(`/reviews/${reviewId}`);
  return unwrapResponse<ReviewDetail>(response);
}

export async function updateReview(reviewId: string, data: UpdateReviewRequest) {
  const response = await apiClient.put(`/reviews/${reviewId}`, data);
  return unwrapResponse<ReviewUpdateResponse>(response);
}
