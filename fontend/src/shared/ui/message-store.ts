import { create } from 'zustand';

export type AppMessageTone = 'info' | 'success' | 'warning' | 'error';

export type AppMessage = {
  id: string;
  tone: AppMessageTone;
  text: string;
};

type MessageState = {
  items: AppMessage[];
  push: (message: Omit<AppMessage, 'id'>) => string;
  remove: (id: string) => void;
};

export const useMessageStore = create<MessageState>((set) => ({
  items: [],
  push: (message) => {
    const id = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;
    set((state) => ({
      items: [...state.items, { id, ...message }],
    }));
    return id;
  },
  remove: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
    })),
}));

export function pushMessage(message: Omit<AppMessage, 'id'>) {
  return useMessageStore.getState().push(message);
}

export function removeMessage(id: string) {
  useMessageStore.getState().remove(id);
}
