import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { migrateLegacyPersistedState } from '@/shared/lib/persist-migration';
import type { AuthSession } from './types';

type AuthActions = {
  setSession: (payload: {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
    userId: number;
    publicId: string;
  }) => void;
  updateAccessToken: (accessToken: string, tokenType: string, userId: number) => void;
  setUsernameDraft: (username: string) => void;
  clearSession: () => void;
};

const initialState: AuthSession = {
  accessToken: null,
  refreshToken: null,
  tokenType: null,
  userId: null,
  publicId: null,
  usernameDraft: '',
  isAuthenticated: false,
};

migrateLegacyPersistedState('uli-auth', ['love-mediator-auth']);

export const useAuthStore = create<AuthSession & AuthActions>()(
  persist(
    (set) => ({
      ...initialState,
      setSession: ({ accessToken, refreshToken, tokenType, userId, publicId }) =>
        set((state) => ({
          ...state,
          accessToken,
          refreshToken,
          tokenType,
          userId,
          publicId,
          isAuthenticated: true,
        })),
      updateAccessToken: (accessToken, tokenType, userId) =>
        set((state) => ({
          ...state,
          accessToken,
          tokenType,
          userId,
          isAuthenticated: true,
        })),
      setUsernameDraft: (usernameDraft) =>
        set((state) => ({
          ...state,
          usernameDraft,
        })),
      clearSession: () =>
        set((state) => ({
          ...initialState,
          usernameDraft: state.usernameDraft,
        })),
    }),
    {
      name: 'uli-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        tokenType: state.tokenType,
        userId: state.userId,
        publicId: state.publicId,
        usernameDraft: state.usernameDraft,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
