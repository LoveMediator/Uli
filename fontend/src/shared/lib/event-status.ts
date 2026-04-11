import { EventStatus, type EventStatusValue } from '@/shared/api/types';

const eventStatusLabels: Record<EventStatusValue, string> = {
  [EventStatus.draft]: '草稿',
  [EventStatus.waitingB]: '等待对方处理中',
  [EventStatus.judged]: '已生成裁决',
  [EventStatus.reviewed]: '已复盘',
  [EventStatus.closed]: '已关闭',
};

export function formatEventStatus(status: EventStatusValue | null | undefined) {
  if (!status) {
    return '未知状态';
  }

  return eventStatusLabels[status] ?? status;
}
