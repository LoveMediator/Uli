import { useState } from 'react';
import { useAuth } from '../hooks';

export const LoginExample = () => {
  const { login, isLoading, user, isAuthenticated } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败');
    }
  };

  if (isAuthenticated && user) {
    return (
      <div>
        <h2>欢迎, {user.username}!</h2>
        <p>用户ID: {user.id}</p>
        <p>状态: {user.status}</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>登录</h2>

      <div>
        <label>用户名:</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={isLoading}
        />
      </div>

      <div>
        <label>密码:</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
        />
      </div>

      {error && <div style={{ color: 'red' }}>{error}</div>}

      <button type="submit" disabled={isLoading}>
        {isLoading ? '登录中...' : '登录'}
      </button>
    </form>
  );
};
