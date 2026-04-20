import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CurrentEventSession } from '@/domains/mediation';
import { DEFAULT_RELATIONSHIP_ID } from '@/shared/config/env';
import { migrateLegacyPersistedState } from '@/shared/lib/persist-migration';

export type AppState = {
  relationshipId: string;
  currentEvent: CurrentEventSession | null;
  homeOverlayOpen: boolean;
  calendarExpanded: boolean;
  setRelationshipId: (relationshipId: string) => void;
  setCurrentEvent: (currentEvent: CurrentEventSession | null) => void;
  patchCurrentEvent: (patch: Partial<CurrentEventSession>) => void;
  clearCurrentEvent: () => void;
  setHomeOverlayOpen: (open: boolean) => void;
  setCalendarExpanded: (expanded: boolean) => void;
  resetAppContext: () => void;
};

migrateLegacyPersistedState('uli-app', ['love-mediator-app']);

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      relationshipId: DEFAULT_RELATIONSHIP_ID,
      currentEvent: null,
      homeOverlayOpen: false,
      calendarExpanded: false,
      setRelationshipId: (relationshipId) => set({ relationshipId }),
      setCurrentEvent: (currentEvent) => set({ currentEvent }),
      patchCurrentEvent: (patch) =>
        set((state) => ({
          currentEvent: state.currentEvent ? { ...state.currentEvent, ...patch } : null,
        })),
      clearCurrentEvent: () => set({ currentEvent: null }),
      setHomeOverlayOpen: (homeOverlayOpen) => set({ homeOverlayOpen }),
      setCalendarExpanded: (calendarExpanded) => set({ calendarExpanded }),
      resetAppContext: () =>
        set({
          relationshipId: DEFAULT_RELATIONSHIP_ID,
          currentEvent: null,
          homeOverlayOpen: false,
          calendarExpanded: false,
        }),
    }),
    {
      name: 'uli-app',
      partialize: (state) => ({
        relationshipId: state.relationshipId,
        currentEvent: state.currentEvent,
        calendarExpanded: state.calendarExpanded,
      }),
    },
  ),
);
