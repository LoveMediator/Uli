import { useAppStore } from '@/app/model/app-store';

export function useCalendarState() {
  const relationshipId = useAppStore((state) => state.relationshipId);
  const calendarExpanded = useAppStore((state) => state.calendarExpanded);
  const setCalendarExpanded = useAppStore((state) => state.setCalendarExpanded);

  return {
    relationshipId,
    calendarExpanded,
    setCalendarExpanded,
  };
}
