import {
  calendarApi as domainCalendarApi,
  getCalendar,
  getReview,
  getReviewsByDate,
  updateReview,
} from '@/domains/calendar';

export { getCalendar, getReview, getReviewsByDate, updateReview };

export const calendarApi = domainCalendarApi;
