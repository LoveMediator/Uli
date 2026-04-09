import { useAppStore } from '@/app/model/app-store';

export function useCurrentEvent() {
  const currentEvent = useAppStore((state) => state.currentEvent);
  const setCurrentEvent = useAppStore((state) => state.setCurrentEvent);
  const patchCurrentEvent = useAppStore((state) => state.patchCurrentEvent);
  const clearCurrentEvent = useAppStore((state) => state.clearCurrentEvent);
  const relationshipId = useAppStore((state) => state.relationshipId);
  const setRelationshipId = useAppStore((state) => state.setRelationshipId);

  return {
    currentEvent,
    relationshipId,
    setRelationshipId,
    setCurrentEvent,
    patchCurrentEvent,
    clearCurrentEvent,
  };
}
