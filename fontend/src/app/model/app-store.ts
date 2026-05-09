import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CurrentEventSession } from '@/domains/mediation';
import type { RelationshipSummary } from '@/shared/api/types';
import { DEFAULT_RELATIONSHIP_ID } from '@/shared/config/env';
import { migrateLegacyPersistedState } from '@/shared/lib/persist-migration';

export type AppState = {
  relationshipId: string;
  activeRelationship: RelationshipSummary | null;
  currentEvent: CurrentEventSession | null;
  homeOverlayOpen: boolean;
  calendarExpanded: boolean;
  setRelationshipId: (relationshipId: string) => void;
  setActiveRelationship: (relationship: RelationshipSummary | null) => void;
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
      activeRelationship: null,
      currentEvent: null,
      homeOverlayOpen: false,
      calendarExpanded: false,
      setRelationshipId: (relationshipId) => set({ relationshipId }),
      setActiveRelationship: (activeRelationship) => set({ activeRelationship }),
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
          activeRelationship: null,
          currentEvent: null,
          homeOverlayOpen: false,
          calendarExpanded: false,
        }),
    }),
    {
      name: 'uli-app',
      partialize: (state) => ({
        relationshipId: state.relationshipId,
        activeRelationship: state.activeRelationship,
        currentEvent: state.currentEvent,
        calendarExpanded: state.calendarExpanded,
      }),
    },
  ),
);
