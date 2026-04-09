import { useMutation } from '@tanstack/react-query';
import { authApi } from '@/domains/auth/api/auth-api';
import { useAuthStore } from '@/domains/auth/model/auth-store';
import { getErrorMessage } from '@/shared/lib';

export function useAuth() {
  const authState = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      authState.setSession(data);
    },
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      const refreshToken = authState.refreshToken;
      if (refreshToken) {
        await authApi.logout({ refreshToken });
      }
    },
    onSettled: () => {
      authState.clearSession();
    },
  });

  return {
    ...authState,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
    loginError: getErrorMessage(loginMutation.error, ''),
    registerError: getErrorMessage(registerMutation.error, ''),
    logoutError: getErrorMessage(logoutMutation.error, ''),
  };
}
