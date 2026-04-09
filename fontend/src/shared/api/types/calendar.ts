export interface CalendarDayCount {
  date: string;
  count: number;
}

export interface CalendarMonthData {
  month: string;
  days: CalendarDayCount[];
}

export interface ReviewListItem {
  reviewId: string;
  eventId: string;
  title: string | null;
  updatedAt: string;
}

export interface ReviewDetail {
  reviewId: string;
  eventId: string;
  content: string;
  source: string;
  createdAt: string;
  updatedAt: string;
}

export interface UpdateReviewRequest {
  content: string;
}

export interface ReviewUpdateResponse {
  reviewId: string;
  updatedAt: string;
  updatedBy: string;
}
