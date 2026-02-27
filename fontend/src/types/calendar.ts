// 复盘记录
export interface Review {
  id: string;
  eventId: string;
  relationshipId: string;
  title: string;
  summary: string;
  aResponsibility: number;
  bResponsibility: number;
  tags: string[];
  isShared: boolean;
  createdAt: string;
  updatedAt: string;
}

// 日历日期项
export interface CalendarDay {
  date: string;
  hasReviews: boolean;
  reviewCount: number;
}

// 日历月份数据
export interface CalendarMonth {
  year: number;
  month: number;
  days: CalendarDay[];
}

// 更新复盘请求
export interface UpdateReviewRequest {
  title?: string;
  summary?: string;
  tags?: string[];
  isShared?: boolean;
}
