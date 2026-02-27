import { useState, useEffect } from 'react';
import { useEvents } from '../hooks';

export const EventsExample = () => {
  const {
    events,
    isLoading,
    error,
    fetchEvents,
    createEvent,
  } = useEvents();

  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createEvent(title, message);
      setTitle('');
      setMessage('');
      await fetchEvents(); // 刷新列表
    } catch (err) {
      console.error('创建失败', err);
    }
  };

  return (
    <div>
      <h2>事件管理</h2>

      {/* 创建事件表单 */}
      <form onSubmit={handleCreate}>
        <h3>创建新事件</h3>
        <div>
          <label>标题:</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="今天的争吵"
          />
        </div>
        <div>
          <label>初始消息:</label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="描述发生了什么..."
          />
        </div>
        <button type="submit" disabled={isLoading}>
          创建事件
        </button>
      </form>

      {/* 事件列表 */}
      <div>
        <h3>事件列表</h3>
        {isLoading && <p>加载中...</p>}
        {error && <p style={{ color: 'red' }}>{error}</p>}

        {events.length === 0 ? (
          <p>暂无事件</p>
        ) : (
          <ul>
            {events.map((event) => (
              <li key={event.id}>
                <strong>ID:</strong> {event.id} |
                <strong> 状态:</strong> {event.status} |
                <strong> 创建时间:</strong> {new Date(event.createdAt).toLocaleString()}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
