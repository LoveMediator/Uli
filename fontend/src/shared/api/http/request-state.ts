import { create } from 'zustand';

type RequestState = {
  pendingCount: number;
  start: () => void;
  finish: () => void;
};

export const useRequestStateStore = create<RequestState>((set) => ({
  pendingCount: 0,
  start: () =>
    set((state) => ({
      pendingCount: state.pendingCount + 1,
    })),
  finish: () =>
    set((state) => ({
      pendingCount: Math.max(0, state.pendingCount - 1),
    })),
}));

export function beginTrackedRequest() {
  useRequestStateStore.getState().start();
}

export function endTrackedRequest() {
  useRequestStateStore.getState().finish();
}
