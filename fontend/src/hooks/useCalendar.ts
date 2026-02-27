import { useState, useCallback } from 'react';
import { Review, CalendarMonth } from '../types/calendar';
import * as calendarApi from '../api/calendar';

interface UseCalendarReturn {
  calendarData: CalendarMonth | null;
  reviews: Review[];
  currentReview: Review | null;
  isLoading: boolean;
  error: string | null;
  fetchCalendar: (year: number, month: number) => Promise<void>;
  fetchReviewsByDate: (date: string) => Promise<void>;
  fetchReview: (reviewId: string) => Promise<void>;
  updateReview: (reviewId: string, data: Partial<Review>) => Promise<void>;
  deleteReview: (reviewId: string) => Promise<void>;
}

export const useCalendar = (): UseCalendarReturn => {
  const [calendarData, setCalendarData] = useState<CalendarMonth | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [currentReview, setCurrentReview] = useState<Review | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 获取日历数据
  const fetchCalendar = useCallback(async (year: number, month: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await calendarApi.getCalendar(year, month);
      setCalendarData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch calendar');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 获取指定日期的复盘列表
  const fetchReviewsByDate = useCallback(async (date: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await calendarApi.getReviewsByDate(date);
      setReviews(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch reviews');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 获取复盘详情
  const fetchReview = useCallback(async (reviewId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await calendarApi.getReview(reviewId);
      setCurrentReview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch review');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 更新复盘
  const updateReview = useCallback(async (reviewId: string, data: Partial<Review>) => {
    setIsLoading(true);
    setError(null);
    try {
      const updated = await calendarApi.updateReview(reviewId, data);
      setCurrentReview(updated);
      setReviews((prev) => prev.map((r) => (r.id === reviewId ? updated : r)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update review');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 删除复盘
  const deleteReview = useCallback(async (reviewId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await calendarApi.deleteReview(reviewId);
      setReviews((prev) => prev.filter((r) => r.id !== reviewId));
      if (currentReview?.id === reviewId) {
        setCurrentReview(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete review');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [currentReview]);

  return {
    calendarData,
    reviews,
    currentReview,
    isLoading,
    error,
    fetchCalendar,
    fetchReviewsByDate,
    fetchReview,
    updateReview,
    deleteReview,
  };
};
