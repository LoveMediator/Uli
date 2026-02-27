import { useState, useEffect, useCallback } from 'react';
import { User } from '../types/auth';
import * as authApi from '../api/auth';
import { getAccessToken, clearTokens } from '../api/client';

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 获取当前用户信息
  const refreshUser = useCallback(async () => {
    try {
      const token = getAccessToken();
      if (!token) {
        setUser(null);
        return;
      }

      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      setUser(null);
      clearTokens();
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 登录
  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await authApi.login({ username, password });
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 注册
  const register = useCallback(async (username: string, password: string, confirmPassword: string) => {
    setIsLoading(true);
    try {
      const response = await authApi.register({ username, password, confirmPassword });
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 登出
  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await authApi.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 初始化时检查登录状态
  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };
};
