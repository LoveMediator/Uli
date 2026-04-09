import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { calendarApi } from '@/domains/calendar/api/calendar-api';
import { useCalendarState } from '@/domains/calendar/model/use-calendar-state';
import { ReviewEditorDrawer } from '@/domains/calendar/ui/ReviewEditorDrawer';
import { buildMonthGrid, cn, formatDisplayDate, formatMonthHeading, getErrorMessage, toDateKey, toMonthKey } from '@/shared/lib';
import { BottomSheet, Button, Card } from '@/shared/ui';

export function CalendarPage() {
  const { relationshipId, calendarExpanded, setCalendarExpanded } = useCalendarState();
  const [cursorDate, setCursorDate] = useState(() => new Date());
  const [selectedDateState, setSelectedDate] = useState(() => toDateKey(new Date()));
  const [activeReviewId, setActiveReviewId] = useState<string | null>(null);
  const monthKey = toMonthKey(cursorDate);
  const selectedDate = selectedDateState.startsWith(monthKey) ? selectedDateState : `${monthKey}-01`;
  const monthGrid = buildMonthGrid(monthKey);
  const heading = formatMonthHeading(monthKey);

  const calendarQuery = useQuery({
    queryKey: ['calendar', monthKey, relationshipId],
    queryFn: () => calendarApi.getCalendar(monthKey, relationshipId),
  });

  const reviewListQuery = useQuery({
    queryKey: ['calendar-reviews', selectedDate, relationshipId],
    queryFn: () => calendarApi.getReviewsByDate(selectedDate, relationshipId),
    enabled: !!selectedDate,
  });

  const countByDate = useMemo(
    () => new Map((calendarQuery.data?.days ?? []).map((day) => [day.date, day.count])),
    [calendarQuery.data?.days],
  );

  return (
    <div className="relative flex h-full flex-col overflow-hidden bg-milk-50">
      <div className="flex-1 bg-milk-50 px-6 pt-14">
        <div className="mb-6 flex items-end justify-between">
          <div>
            <h2 className="text-3xl font-extrabold tracking-tight text-coffee-900">{heading.monthLabel}</h2>
            <span className="text-sm font-bold text-gray-400">{heading.yearLabel}</span>
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              className="rounded-full px-3 py-2"
              onClick={() => setCursorDate((current) => new Date(current.getFullYear(), current.getMonth() - 1, 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="secondary"
              className="rounded-full px-3 py-2"
              onClick={() => setCursorDate((current) => new Date(current.getFullYear(), current.getMonth() + 1, 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="mb-3 grid grid-cols-7 text-center">
          {['日', '一', '二', '三', '四', '五', '六'].map((label) => (
            <span key={label} className="text-xs font-bold text-gray-300">
              {label}
            </span>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-y-4 text-center">
          {Array.from({ length: monthGrid.leadingEmptyCells }).map((_, index) => (
            <div key={`blank-${index}`} />
          ))}
          {monthGrid.days.map((day) => {
            const count = countByDate.get(day.dateKey) ?? 0;
            const isSelected = day.dateKey === selectedDate;
            const isToday = day.dateKey === toDateKey(new Date());

            return (
              <button
                key={day.dateKey}
                className="flex min-h-[54px] flex-col items-center gap-1"
                onClick={() => setSelectedDate(day.dateKey)}
              >
                <span
                  className={cn(
                    'flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium text-coffee-800 transition',
                    isToday && 'bg-coffee-800 font-bold text-white shadow-lg',
                    isSelected && !isToday && 'border border-accent-pink bg-accent-pink/10 text-coffee-900',
                    count > 0 && !isSelected && !isToday && 'border border-red-200 bg-red-50 text-red-700',
                  )}
                >
                  {day.day}
                </span>
                {count > 0 ? <span className="text-[10px] font-bold text-red-300">{count} 条</span> : <span className="text-[10px] text-transparent">0</span>}
              </button>
            );
          })}
        </div>
      </div>

      <BottomSheet expanded={calendarExpanded} onToggle={() => setCalendarExpanded(!calendarExpanded)}>
        <div className="flex-1 overflow-y-auto px-6 pb-10">
          <div className="mb-6 rounded-3xl bg-milk-50 p-4">
            <p className="text-sm font-bold text-coffee-900">今日心情</p>
            <div className="mt-3 grid grid-cols-4 gap-3">
              {['😆', '🙂', '🥺', '😤'].map((emoji) => (
                <div key={emoji} className="flex aspect-square flex-col items-center justify-center rounded-2xl border border-gray-100 bg-white text-2xl shadow-sm">
                  {emoji}
                </div>
              ))}
            </div>
          </div>

          <Card className="space-y-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.3em] text-coffee-800/40">Day Reviews</p>
              <h3 className="mt-2 text-lg font-extrabold text-coffee-900">{formatDisplayDate(selectedDate)}</h3>
            </div>

            {calendarQuery.error ? (
              <p className="text-sm font-semibold text-red-400">{getErrorMessage(calendarQuery.error)}</p>
            ) : null}

            {reviewListQuery.isLoading ? (
              <p className="text-sm text-coffee-800/60">正在加载这一天的复盘记录...</p>
            ) : null}

            {reviewListQuery.data?.items.length ? (
              <div className="space-y-3">
                {reviewListQuery.data.items.map((item) => (
                  <button
                    key={item.reviewId}
                    className="w-full rounded-3xl border border-milk-100 bg-white px-4 py-4 text-left transition hover:bg-milk-50"
                    onClick={() => setActiveReviewId(item.reviewId)}
                  >
                    <p className="text-sm font-bold text-coffee-900">{item.title ?? '未命名复盘'}</p>
                    <p className="mt-2 text-xs leading-6 text-coffee-800/60">
                      eventId: {item.eventId} · 更新于 {new Date(item.updatedAt).toLocaleString('zh-CN')}
                    </p>
                  </button>
                ))}
              </div>
            ) : null}

            {reviewListQuery.data && reviewListQuery.data.items.length === 0 ? (
              <p className="text-sm leading-7 text-coffee-800/60">这一天还没有复盘记录，等事件裁判完成后会自动沉淀到这里。</p>
            ) : null}
          </Card>
        </div>
      </BottomSheet>

      <ReviewEditorDrawer
        key={activeReviewId ?? 'empty'}
        reviewId={activeReviewId}
        open={!!activeReviewId}
        onClose={() => setActiveReviewId(null)}
        onUpdated={() => {
          void reviewListQuery.refetch();
        }}
      />
    </div>
  );
}
