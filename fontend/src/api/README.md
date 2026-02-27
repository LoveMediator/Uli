# LoveMediator API 层使用说明

## 目录结构

```
src/
├── api/                    # API 请求层
│   ├── client.ts           # Axios 实例配置
│   ├── auth.ts             # 认证 API
│   ├── events.ts           # 事件/调解 API
│   ├── calendar.ts         # 日历 API
│   ├── elf.ts              # 小精灵互动 API
│   └── index.ts            # 统一导出
├── types/                  # TypeScript 类型定义
│   ├── api.ts              # 通用响应结构
│   ├── auth.ts             # 认证类型
│   ├── event.ts            # 事件类型
│   ├── calendar.ts         # 日历类型
│   ├── elf.ts              # 小精灵类型
│   └── enums.ts            # 枚举定义
└── hooks/                  # React Hooks
    ├── useAuth.ts          # 认证 Hook
    ├── useEvents.ts        # 事件 Hook
    ├── useCalendar.ts      # 日历 Hook
    └── index.ts            # 统一导出
```

## 快速开始

### 1. 环境配置

复制 `.env.example` 为 `.env.development`：

```bash
cp .env.example .env.development
```

修改 API 地址：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 2. 安装依赖

```bash
npm install
```

### 3. 使用示例

#### 方式一：使用 Hooks（推荐）

```tsx
import { useAuth, useEvents } from './hooks';

function LoginPage() {
  const { login, isLoading, user } = useAuth();

  const handleLogin = async () => {
    try {
      await login('username', 'password');
      console.log('登录成功', user);
    } catch (error) {
      console.error('登录失败', error);
    }
  };

  return (
    <button onClick={handleLogin} disabled={isLoading}>
      {isLoading ? '登录中...' : '登录'}
    </button>
  );
}
```

#### 方式二：直接调用 API

```tsx
import * as authApi from './api/auth';
import * as eventsApi from './api/events';

// 登录
const handleLogin = async () => {
  try {
    const response = await authApi.login({
      username: 'alice',
      password: 'Pass123456'
    });
    console.log('Token:', response.accessToken);
  } catch (error) {
    console.error('登录失败', error);
  }
};

// 创建事件
const createNewEvent = async () => {
  try {
    const event = await eventsApi.createEvent({
      title: '今天的争吵',
      initialMessage: '我们因为晚饭吃什么吵起来了'
    });
    console.log('事件创建成功', event);
  } catch (error) {
    console.error('创建失败', error);
  }
};
```

## API 模块说明

### 认证模块（auth.ts）

```typescript
// 注册
await register({ username, password, confirmPassword });

// 登录
await login({ username, password });

// 登出
await logout();

// 刷新 Token
await refreshAccessToken({ refreshToken });

// 获取当前用户
await getCurrentUser();
```

### 事件模块（events.ts）

```typescript
// 创建事件
await createEvent({ title, initialMessage });

// 获取事件列表
await getEvents();

// 获取事件详情
await getEvent(eventId);

// 发送私聊消息（A方分析）
await sendPrivateChat(eventId, { message });

// 提交快照A（冻结）
await commitSnapshotA(eventId, { title, description });

// B方同意/不同意
await submitBAgreement(eventId, { agree, reason });

// 提交快照B
await commitSnapshotB(eventId, { title, description });

// 获取裁判结果
await getJudgeResult(eventId);

// 发送复盘消息
await sendFollowupChat(eventId, { message });
```

### 日历模块（calendar.ts）

```typescript
// 获取日历数据
await getCalendar(year, month);

// 获取指定日期的复盘列表
await getReviewsByDate('2026-02-27');

// 获取复盘详情
await getReview(reviewId);

// 更新复盘
await updateReview(reviewId, { title, summary, tags, isShared });

// 删除复盘
await deleteReview(reviewId);
```

### 小精灵模块（elf.ts）

```typescript
// 小精灵传话
await relayMessage({ targetUserId, originalMessage });

// 过激语言检测
await moderateMessage({ message });
```

## Hooks 使用说明

### useAuth

```tsx
const {
  user,              // 当前用户信息
  isAuthenticated,   // 是否已登录
  isLoading,         // 加载状态
  login,             // 登录方法
  register,          // 注册方法
  logout,            // 登出方法
  refreshUser        // 刷新用户信息
} = useAuth();
```

### useEvents

```tsx
const {
  events,            // 事件列表
  currentEvent,      // 当前事件
  isLoading,         // 加载状态
  error,             // 错误信息
  fetchEvents,       // 获取事件列表
  fetchEvent,        // 获取单个事件
  createEvent,       // 创建事件
  sendPrivateChat,   // 发送私聊
  commitSnapshotA,   // 提交快照A
  submitBAgreement,  // B方同意
  commitSnapshotB,   // 提交快照B
  getJudgeResult,    // 获取裁判结果
  sendFollowupChat   // 发送复盘消息
} = useEvents();
```

### useCalendar

```tsx
const {
  calendarData,      // 日历数据
  reviews,           // 复盘列表
  currentReview,     // 当前复盘
  isLoading,         // 加载状态
  error,             // 错误信息
  fetchCalendar,     // 获取日历
  fetchReviewsByDate,// 获取指定日期复盘
  fetchReview,       // 获取复盘详情
  updateReview,      // 更新复盘
  deleteReview       // 删除复盘
} = useCalendar();
```

## Token 管理

API 客户端自动处理 Token：

- **自动注入**：请求时自动在 Header 中添加 `Authorization: Bearer <token>`
- **自动刷新**：Token 过期时自动调用 refresh 接口获取新 Token
- **自动存储**：Token 存储在 localStorage 中，页面刷新后自动恢复

手动管理 Token：

```typescript
import { setTokens, getAccessToken, clearTokens } from './api/client';

// 设置 Token
setTokens(accessToken, refreshToken);

// 获取 Token
const token = getAccessToken();

// 清除 Token
clearTokens();
```

## 错误处理

所有 API 调用都会抛出错误，需要使用 try-catch 捕获：

```typescript
try {
  await login({ username, password });
} catch (error) {
  if (error instanceof Error) {
    console.error(error.message);
  }
}
```

常见错误码：

- `1001` - 参数校验失败
- `1002` - 资源不存在
- `2001` - 认证失败
- `2002` - 无权限
- `3001` - 用户名已存在
- `5000` - 系统内部错误

## 类型安全

所有 API 都有完整的 TypeScript 类型定义：

```typescript
import { Event, EventStatus } from './types/event';
import { User, UserStatus } from './types/auth';
import { Review } from './types/calendar';

// 类型推断
const event: Event = await createEvent({ title, initialMessage });
console.log(event.status); // EventStatus 枚举
```

## 注意事项

1. **环境变量**：确保正确配置 `VITE_API_BASE_URL`
2. **Token 过期**：Token 过期会自动刷新，刷新失败会跳转登录页
3. **请求超时**：默认超时时间 30 秒
4. **并发请求**：支持多个请求并发，自动处理 Token 刷新竞态
5. **错误处理**：所有 API 都需要 try-catch 处理错误
